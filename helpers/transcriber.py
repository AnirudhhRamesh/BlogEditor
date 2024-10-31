import json
import assemblyai as aai
from schemas.file import Utterances, Utterance, Transcript


class Transcriber:
    """
    Service class to transcribe audio files
    """

    def __init__(self, config, llm):
        """
        Initialize the Transcriber
        """
        aai.settings.api_key = config["ASSEMBLYAI_API_KEY"]
        self.llm = llm

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
        
        # Map AssemblyAI transcript to our Transcript schema
        utterances = [
            Utterance(
                confidence=utterance.confidence,
                end=utterance.end,
                speaker=utterance.speaker,
                start=utterance.start,
                text=utterance.text
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

        prompt = f"""Your task is to identify the guest speaker in a conversation transcript between a guest and a host, and return their label. The conversation is between two people, A and B.

        Generally, the host asks questions about the guest's background, story, experiences.

        Generally, the guest answers the host's questions, and responds with their background, story, experiences.

        Identify and return the speaker label. Return 'A' if the guest is the first to speak. Otherwise, return 'B'.

        Return in json format with the key 'guest' and the value 'A' or 'B'.

        Here is an example transcript:
        <transcript>
            A: Recording. Okay. Yeah. Again, it's like a chat. I'll share the blog with you first, and you can review everything before anything's published. So you have full control.
            B: The goal is not to publish the recording. Right. It's just like you to make an article or a post out of it.
            A: Exactly. Fully private. It's just to make it trans up to make the blog.
            B: Yeah, sounds good. As long as you show me the post before the blog, before posting, you're like, I'm done.
            A: Yeah, absolutely. Yeah. Maybe we can start. We don't have too much time, but maybe we can just go ahead. Where did you grow up?
            B: I grew up in the countryside of France, near mess, which is like 120,000 Abigail city, not far from Germany. It was very kind of like a small town, like 10,000 people. Yeah, that's where I grew up until I was 19.
            A: And then you came to EPFL for Mikotech microengineering, right?
        </transcript>

        Here is the generated output:
        <response>
            {{"guest": "B"}}
        </response>

        Analyze the following transcript:
        {transcript}
        """

        # Identify the guest speaker
        guest = self.llm.structured_prompt(prompt, model="sonnet")

        if guest['guest'] not in ['A', 'B']:
            guest['guest'] = 'B' #Fallback to B

        guest_speaker = guest['guest']

        # Parse the transcript by labelling using the guest speaker
        annotated_transcript = ""

        for utterance in utterances.utterances:
            if utterance.speaker == guest_speaker:
                annotated_transcript += f"{utterance.text} \n"
            else:
                annotated_transcript += f"## {utterance.text} \n"

        return Transcript(text=annotated_transcript)
