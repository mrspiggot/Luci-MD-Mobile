"""
This module provides a set of classes for processing documents, building vector stores,
and generating articles using AI models within a Streamlit UI.
"""

import streamlit as st
from langchain.document_loaders import PyPDFLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
import tempfile

from dotenv import load_dotenv
import os

class LuciDocumentProcessor:
    """
    A class to process document files, specifically for extracting text from PDF files.
    """
    def __init__(self, file_data):
        """
        Initializes the LuciDocumentProcessor with the file data.

        :param file_data: The binary data of the file to be processed.
        """
        self.file_data = file_data

    def get_text(self):
        """
        Extracts and returns the text from the loaded PDF file.

        :return: A string containing all the text extracted from the PDF file.
        """
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(self.file_data.getvalue())
            loader = PyPDFLoader(os.path.abspath(temp_file.name))
            pages = loader.load_and_split()
            return "".join(t.page_content for t in pages)

class LuciVectorStoreManager:
    """
    Manages the creation and retrieval of vector stores for text data.
    """
    def __init__(self, text):
        """
        Initializes the LuciVectorStoreManager with text to be vectorized.

        :param text: The text to build the vector store from.
        """
        self.text = text

    def build_vectorstore(self):
        """
        Builds and returns a vector store from the provided text.

        :return: A retriever object for the constructed vector store.
        """
        vectorstore = FAISS.from_texts([self.text], embedding=OpenAIEmbeddings())
        return vectorstore.as_retriever()

class LuciUIController:
    """
    Handles the user interface and interaction in the Streamlit app.
    """
    def __init__(self):
        """
        Initializes the LuciUIController, setting up the UI components.
        """
        self.sidebar = st.sidebar
        self.model_options = ["gpt-4", "gpt-3.5-turbo-0613", "Gemini", "Luci-FT-Gen", "Claude2"]
        self.setup_ui()

    def setup_ui(self):
        """
        Sets up the user interface elements in the Streamlit sidebar and main area.
        """
        logo = "color_lucidate.png"
        st.sidebar.image(logo, width=120)
        self.sidebar.header("AI Settings")
        self.selected_model = self.sidebar.selectbox("Select AI Model", self.model_options)
        self.temperature = self.sidebar.slider("Temperature", 0.0, 1.0, 0.7)
        self.sidebar.header("Upload Files")
        self.sample_article = self.sidebar.file_uploader("Sample Article", type="pdf")
        self.essays = self.sidebar.file_uploader("Source documents", type=["pdf"], accept_multiple_files=True)
        st.header("Article Generator:")
        self.prompt_text = st.text_area("Edit Prompt", """Write an article using the style of this document {style}. Replicate its approach to generating titles and subheading. Ensure that the subheadings relate to the content that follows to be as helpful as possible to the reader.  Think carefully about the principles of a good headline and apply these principles to make the headline as relevant, catchy and compelling as you can to encourage readership. Put a newline after each title and subheading. For the article base it only on the following content: {context}. Use only the content do not publish the names of the people responsible for the research.""", height=200)

class LuciArticleGenerator:
    """
    Generates articles using the provided AI model and user inputs.
    """
    def __init__(self, ui_controller):
        """
        Initializes the LuciArticleGenerator with a reference to the UI controller.

        :param ui_controller: An instance of LuciUIController for UI interactions.
        """
        self.ui = ui_controller

    def generate(self):
        """
        Generates an article based on the user inputs and outputs the result to the Streamlit interface.
        """
        # If a sample article is uploaded, process it to extract the text.
        # Otherwise, set style_text to an empty string.
        style_text = LuciDocumentProcessor(self.ui.sample_article).get_text() if self.ui.sample_article else ""

        # If one or more essays are uploaded, process each to extract their text.
        # Combine the text of all essays into one string, or set source_texts to an empty list if no essays are uploaded.
        source_texts = [LuciDocumentProcessor(essay).get_text() for essay in self.ui.essays] if self.ui.essays else []

        # Use the combined text from the essays to build a vector store for content retrieval.
        source_retriever = LuciVectorStoreManager(" ".join(source_texts)).build_vectorstore()

        # Use the text from the sample article to build a vector store for style retrieval.
        style_retriever = LuciVectorStoreManager(style_text).build_vectorstore()

        # Create a prompt template from the UI's prompt text.
        prompt = ChatPromptTemplate.from_template(self.ui.prompt_text)

        # Initialize the ChatOpenAI model using the selected AI model from the UI.
        model = ChatOpenAI(model=self.ui.selected_model)

        # Build a chain of operations using LangChain Expression Language (LCEL).
        # This chain combines the context from source_retriever, the style from style_retriever,
        # applies the prompt template, invokes the selected AI model, and parses the output to a string.
        result_chain = ({"context": source_retriever, "style": style_retriever} | prompt | model | StrOutputParser()).invoke("Please write an article in this style")

        # Output the result to the Streamlit interface.
        st.write(result_chain)



if __name__ == "__main__":
    load_dotenv()
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    ui_controller = LuciUIController()
    if st.button("Run"):
        LuciArticleGenerator(ui_controller).generate()

# Alternative prompt scratch area
#
#
# self.prompt_text = st.text_area("Edit Prompt", """Write an article using the style of this document {style}. Replicate its approach to generating titles and subheading. Put a newline after each title and subheading. For the article base it only on the following content: {context}""")
