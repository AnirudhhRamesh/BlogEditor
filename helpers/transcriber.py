import assemblyai as aai
from schemas.file import Utterances, Utterance, Transcript, Word
from schemas.prompt import SimpleResponse

class Transcriber:
    """
    Service class to transcribe audio files
    """

    def __init__(self, config, llm, prompts):
        """
        Initialize the Transcriber
        """
        aai.settings.api_key = config["ASSEMBLYAI_API_KEY"]
        self.llm = llm
        self.prompts = prompts

    def transcribe(self, audio_file_path: str):
        """
        Transcribe the given audio file (hardcoded to use AssemblyAI with 2 speakers for now)
        """
        config = aai.TranscriptionConfig(speaker_labels=True, speakers_expected=2)
        transcriber = aai.Transcriber()

        transcript = transcriber.transcribe(
            audio_file_path,
            config=config
        )
        
        print(transcript.utterances[0])
        # Map AssemblyAI transcript to our Transcript schema
        utterances = [
            Utterance(
                confidence=utterance.confidence,
                end=utterance.end,
                speaker=utterance.speaker,
                start=utterance.start,
                text=utterance.text,
                words=[Word(
                    text=word.text,
                    start=word.start,
                    end=word.end,
                    confidence=word.confidence,
                    speaker=word.speaker
                ) for word in utterance.words]
            )
            for utterance in transcript.utterances
        ]
        
        return Utterances(utterances=utterances)

    def generate_transcript(self, utterances: Utterances) -> Transcript:
        """
        Generate a transcript from the given utterances, by identifying the interviewer (h2) and guest (p).
        """
        # Merge the utterances into a single transcript
        transcript = " ".join([f"Speaker {utterance.speaker}: {utterance.text}" for utterance in utterances.utterances])

        # Analyze the transcript using LLM 'haiku'
        # Use CoT reasoning in the prompt even and then Pydantic validation for a more sophisticated prompt?
        prompt = self.prompts.identify_speaker_prompt(transcript)

        # Identify the guest speaker
        guest = self.llm.prompt(prompt.text, model=prompt.model, schema=SimpleResponse)

        if guest.response not in ['A', 'B']:
            guest.response = 'B' #Fallback to B

        guest_speaker = guest.response

        # Parse the transcript by labelling using the guest speaker
        annotated_transcript = ""
        questions = ""

        for utterance in utterances.utterances:
            if utterance.speaker == guest_speaker:
                annotated_transcript += f"{utterance.text} \n"
            else:
                annotated_transcript += f"## {utterance.text} \n"
                questions += f"## {utterance.text} \n \n"

        return Transcript(text=annotated_transcript)
