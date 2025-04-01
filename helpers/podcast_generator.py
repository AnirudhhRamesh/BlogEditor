from schemas.file import File
from elevenlabs.client import ElevenLabs
from llms.llm_service import LLMService
import random
import os
from moviepy import AudioFileClip, ColorClip, CompositeVideoClip, TextClip

class PodcastGenerator:
    """
    Service class to generate podcasts
    """

    def __init__(self, config, llm, prompts):
        """
        Initialize the PodcastGenerator
        """
        self.config = config
        self.client = ElevenLabs(api_key=config["ELEVENLABS_API_KEY"])
        self.llm = llm
        self.prompts = prompts

    def generate(self, file: File) -> None:
        """
        Generate a podcast from the given blog. WIP
        """
        # You can use voice cloning to clone the guest's voices!

        # Use the blog.metadata.utterances and blog.metadata.guest to generate a podcast
        response = self.client.voices.get_all()
        print(f"Voices: {response}")

        # Split content into lines and categorize them as interviewer/guest parts
        lines = file.blog.content.split('\n')
        interviewer_parts = []
        guest_parts = []
        current_guest_response = []

        for line in lines:
            # Skip main headings (single #)
            if line.startswith('# '):
                continue
            elif line.startswith('###'):
                # If we have collected any guest response, save it
                if current_guest_response:
                    guest_parts.append(' '.join(current_guest_response))
                    current_guest_response = []
                # Add interviewer question (remove the ### prefix)
                interviewer_parts.append(line.lstrip('#').strip())
            elif line.strip():  # Only include non-empty lines
                current_guest_response.append(line)

        # Add the final guest response if any
        if current_guest_response:
            guest_parts.append(' '.join(current_guest_response))


        print(f"Interviewer parts: {interviewer_parts}")
        print(f"Guest parts: {guest_parts}")

        total_audio_bytes = b""

        for i in range(2):
            # Generate the interviewer question
            audio = self.client.generate(text=interviewer_parts[i], voice=response.voices[1])
            audio_bytes = b"".join(list(audio))
            total_audio_bytes += audio_bytes

            # Generate the guest response
            audio = self.client.generate(text=guest_parts[i], voice=response.voices[2])
            audio_bytes = b"".join(list(audio))
            total_audio_bytes += audio_bytes

        # Save the audio file to the output directory
        random_id = random.randint(1000, 9999)
        output_path = f"/Users/anirudhh/Documents/axd_blogs_voice/podcast_{random_id}.mp3"
        with open(output_path, "wb") as f:
            f.write(total_audio_bytes)
        return audio

    def clone_speaker(self, file: File) -> None:
        """
        Clone the speaker's voice
        """
        # Get the utterances that belong to the guest
        guest_utterances = [utterance for utterance in file.metadata.utterances.utterances if utterance.speaker == file.blog.metadata.guest]

        # Split the audio file into chunks based on the guest_utterances start + end timestamps

        # Join the chunks back together which are longer than 10 seconds

        # Use the AssemblyAI API to clone the guest voice

        raise NotImplementedError("Not implemented")
    
    def smart_cut(self, file: File) -> None:
        """
        Smartly cut thet transcript segments by using the utterances + cross-matching the blog content

        Any papers on this? 
        """
        
        raise NotImplementedError("Not implemented")

    def generate_intro(self, file: File) -> None:
        """
        Generate an intro for the podcast with both audio and video
        """
        
        speaker_voice = self.client.voices.get(voice_id="5HDW0qbyNwiQkijnIHQ4")
        
        # TODO remove (for testing)
        # voices = self.client.voices.get_all()
        # speaker_voice = voices.voices[0]

        prompt = self.prompts.podcast_intro_prompt(file)
        intro_text = self.llm.prompt(prompt)

        # Generate the intro audio
        audio = self.client.generate(text=intro_text, voice=speaker_voice)
        audio_bytes = b"".join(list(audio))
        random_id = random.randint(1000, 9999)
        
        # Create paths for both audio and video files
        base_path = f"/Users/anirudhh/Documents/Zoom_v2/irina_clip/content/intro_{random_id}"
        audio_path = f"{base_path}.mp3"
        video_path = f"{base_path}.mp4"
        
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        
        # Save the audio file
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        # Create video from audio using updated MoviePy syntax
        audio_clip = AudioFileClip(audio_path)
        
        # Create a simple colored background with updated syntax
        video_clip = ColorClip(
            size=(1920, 1080),
            color=(25, 25, 25),
            duration=audio_clip.duration
        )
        
        # Split intro text into sentences for better presentation
        sentences = [s.strip() for s in intro_text.split('.') if s.strip()]
        
        # Create text clips for each sentence
        text_clips = []
        duration_per_text = audio_clip.duration / len(sentences)
        
        for i, sentence in enumerate(sentences):
            text_clip = TextClip(
                text=sentence,
                font='Arial.ttf',
                font_size=48,
                color='white',
                size=(1600, None),  # Width constraint, height automatic
                method='caption'
            ).with_position(('center', 'center'))
            
            # Add fade in/out effects and set the timing
            start_time = i * duration_per_text
            text_clip = (text_clip
                        .with_start(start_time)
                        .with_duration(duration_per_text))
            
            text_clips.append(text_clip)
        
        # Combine background and text clips
        final_clip = CompositeVideoClip(
            [video_clip] + text_clips
        ).with_audio(audio_clip)
        
        # Write the final video file with modern codec settings
        final_clip.write_videofile(
            video_path,
            fps=12,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            threads=16
        )
        
        # Clean up resources
        audio_clip.close()
        final_clip.close()
        for clip in text_clips:
            clip.close()
        os.remove(audio_path)

        # TODO: Append the intro to the podcast


    def generate_podcast(self, file: File) -> None:
        """
        Generate a podcast from the given blog
        """
        
        voices = self.client.voices.get_all()
        host_voice = self.client.voices.get(voice_id="5HDW0qbyNwiQkijnIHQ4")
        guest_voice = self.client.voices.get(voice_id="cgSgspJ2msm6clMCkdW9")

        blog = file.blog.content
        # Split the blog into h3 (host questions) and p (guest responses)
        lines = blog.split('\n')
        tasks = []

        for line in lines:
            if line.startswith('###'):
                line = line.replace('#', '').strip()
                print(f"Line: {line}")
                if line.strip():
                    if tasks and tasks[-1][0] == 'host':
                        tasks[-1] = ('host', tasks[-1][1] + ' ' + line)
                    else:
                        tasks.append(('host', line))
            else:
                if not line.startswith('#'):
                    if line.strip():
                        if tasks and tasks[-1][0] == 'guest':
                            tasks[-1] = ('guest', tasks[-1][1] + ' ' + line)
                        else:
                            tasks.append(('guest', line))

        print(f"Tasks: {tasks}")

        audio_bytes_list = []
        # Generate the podcast
        for task in tasks:
            if task[0] == 'host':
                audio = self.client.generate(text=task[1], voice=host_voice)
            else:
                audio = self.client.generate(text=task[1], voice=guest_voice)
            audio_bytes = b"".join(list(audio))
            audio_bytes_list.append(audio_bytes)

        # Save the entire audio_bytes to a file
        random_id = random.randint(1000, 9999)
        audio_path = f"/Users/anirudhh/Documents/Zoom_v2/irina_clip/content/podcast_{random_id}.mp3"
        with open(audio_path, "wb") as f:
            f.write(b''.join(audio_bytes_list))

    def generate_outro(self, file: File) -> None:
        """
        Generate an outro for the podcast
        """

        # Recap podcast, add-in shoutouts to sponsors

        # Make a summary of the podcast in the outro
        
        sponsors = {"Founderful"}
        sponsors_prompt = self.prompts.sponsors_prompt(sponsors)
        # Make a shoutout to the sponsors as well


        raise NotImplementedError("Not implemented")
