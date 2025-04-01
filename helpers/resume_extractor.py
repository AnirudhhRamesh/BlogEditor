import logging
from schemas.file import Resume, Guest, File
from schemas.prompt import SimpleResponse, ListResponse
from prompts.prompts import Prompts
import PyPDF2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeExtractor:
    """
    Service class to extract resume data from a PDF in a structured way.
    """

    def __init__(self, llm, prompts):
        """
        Initialize the ResumeExtractor
        """
        self.llm = llm
        self.prompts = prompts

    def extract(self, file: File):
        """
        Extract the resume data from the given PDF file
        """
        text = ""
        
        with open(file.files.resume_file, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()

        prompt = self.prompts.extract_resume_prompt(text)
        return self.llm.prompt(prompt.text, model=prompt.model, schema=Resume)

    def enrich_guest(self, file: File):
        """
        Enrich the guest data with first_name, origin, top companies & universities using the resume
        """

        first_name_prompt = self.prompts.first_name_prompt(file)
        top_companies_prompt = self.prompts.top_companies_prompt(file)
        top_universities_prompt = self.prompts.top_universities_prompt(file)
        origin_prompt = self.prompts.origin_prompt(file)

        first_name = self.llm.prompt(first_name_prompt.text, model=first_name_prompt.model, schema=SimpleResponse)
        top_companies = self.llm.prompt(top_companies_prompt.text, model=top_companies_prompt.model, schema=ListResponse)
        top_universities = self.llm.prompt(top_universities_prompt.text, model=top_universities_prompt.model, schema=ListResponse)
        origin = self.llm.prompt(origin_prompt.text, model=origin_prompt.model, schema=SimpleResponse)

        return Guest(
            first_name=first_name.response,
            top_companies=top_companies.response,
            top_universities=top_universities.response,
            origin=origin.response
        )