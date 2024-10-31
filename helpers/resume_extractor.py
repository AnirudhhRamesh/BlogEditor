import logging

from schemas.file import Resume, ThumbnailResume
from prompts.prompts import Prompts
import PyPDF2

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeExtractor:
    """
    Service class to extract resume data from a PDF in a structured way.
    """

    def __init__(self, llm):
        """
        Initialize the ResumeExtractor
        """
        self.llm = llm

    def extract(self, resume_file_path: str):
        """
        Extract the resume data from the given PDF file
        """
        text = self.parse_pdf(resume_file_path)
        return self.extract_pdf(text)
        
    def parse_pdf(self, file_path: str):
        """
        Parse the given PDF file and return the text
        """
        text = ""
        logging.info(f"Parsing PDF file: {file_path}")
        
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()

        logger.info(f"Parsed PDF: {text}")

        return text

    def extract_pdf(self, text: str):
        """
        Extract the resume data from the given text using LLM and return in a Resume object
        """
        prompt = Prompts.extract_resume_prompt(text)

        response = self.llm.structured_prompt(prompt, model="haiku")
        
        if response is None:
            print("Failed to extract resume")
        
        # Validate the response
        try:
            return Resume.model_validate(response)
        except Exception as e:
            print(f"Failed to validate resume: {e}")
            return None

    def generate_thumbnail_resume(self, resume: Resume):
        """
        Generate a shortened resume (for thumbnails) from the given resume
        """
        # Add first name, companies and universities
        prompt = f"""
            Given the following resume overview, extract the first name, relevant companies and relevant universities.

            For the first_name field, keep only the first word of the name (e.g. "Irina-Madalina" -> "Irina", "Nils" -> "Nils").

            Maintain the order of the companies and universities as they appear in the resume.
            
            If there are many companies, keep at most 6 relevant ones.
            
            For companies, use the acronyms (if they're well-known acronyms) or the shortened version (e.g. NASA JPL instead of NASA Jet Propulsion Laboratory, Bose Corporation as Bose, Quadrature Capital as Quadrature, Amazon Web Services as AWS, but keep QuantCo as QuantCo, Google as Google).
            Keep only well-recognized companies or start-ups that the guest has (co-)founded or student associations that the guest has a high role in (e.g. President, Founder, Lead etc). For example, keep QuantCo (well-recognized tech company), Blue Vision Labs (well-recognized AI company) or AgileTech (co-founder) or impromptu.fun (co-founder/team lead) but not IfTA Ingenieurbüro fur Thermoakustik GmbH (german, not that well-known).
            For universities the student has worked at, unless they are a professor/assistant professor, do not include them (as they are already mentioned in the 'studies' field). If you do include them (as they are e.g. researcher), use the lab name (e.g. SRI Lab) rather than just the university name (e.g. Stanford University).

            Keep only the universities ranked in the global 40 (including EPFL, ETHZ, Stanford, Cambridge, Oxford, MIT, Harvard, etc).
            For universities, use the acronyms (if they're well-known acronyms) or the shortened version (e.g. TUM instead of Technical University of Munich, MIT instead of Massachusetts Institute of Technology, Stanford instead of Stanford University).
            Include universities that the guest did their PhD/Post-doc at here.

            Return only in JSON format with the keys "first_name", "companies", "universities"

            <example>
                <resume>
                    {{
                        "name": "Irina-Madalina Bejan",
                        "studies": ["ETH Zürich, Switzerland, September 2023 - September 2025", "Georgia Institute of Technology, USA, August 2022 - December 2022", "TU Munich, Germany, 2020 - 2023"],
                        "experiences": ["Software Engineer @ QuantCo, November 2023 - Present", "Co-founder @ AgileTech, September 2023 - Present", "Software Engineer @ JetBrains August 2023 - September 2023", "Software Engineer @ IfTA Ingenieurburo fur Thermoakustik GmbH, July 2021 - September 2021", "Software Engineer @ Google, August 2019 - December 2020"],
                        "origin": "Germany",
                        "linkedin_url": "www.linkedin.com/in/nils-cremer"
                    }}
                </resume>
                <output>
                    {{
                        "first_name": "Irina",
                        "companies": ["QuantCo", "AgileTech", "JetBrains", "Google"],
                        "universities": ["ETHZ", "Georgia", "TUM"]
                    }}
                </output>
            </example>

            <resume>
                {resume.model_dump_json()}
            </resume>
        """

        response = self.llm.structured_prompt(prompt, model="sonnet")

        if response is None:
            print("Failed to extract resume data for banner")
            return None

        try:
            return ThumbnailResume.model_validate(response)
        except Exception as e:
            print(f"Failed to validate resume data for banner: {e}")
            return None
