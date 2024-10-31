from schemas.file import File

class PodcastGenerator:
    """
    Service class to generate podcasts
    """

    def __init__(self, config):
        """
        Initialize the PodcastGenerator
        """
        self.config = config
        # Set-up elevenlabs client using the config

    def generate(self, blog: File) -> None:
        """
        Generate a podcast from the given blog. WIP
        """
        # Use the blog.metadata.utterances and blog.metadata.guest to generate a podcast
        raise NotImplementedError("PodcastGenerator not implemented")
