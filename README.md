# Blog Editor

A CLI tool to easily transcribe, generate thumbnails and generate blog assets (title, description, blog, linkedin) for a given .m4a audio file.

## Usage

On MacOS:

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Features

#### Required changes before using:

- Update the Zoom folder path in `blog_editor.py`
- You'll have to write your own `prompts.py` file (I can provide a skeleton if it's needed - reach out here: http://linkedin.com/in/anirudhhramesh/ or anirudhh.ramesh[AT]gmail.com)
- You'll have to include a .env file following the `env.example` file

#### Required files

- Provide .m4a/.mp3 2-person interview (with one guest and one interviewer)
- Provide resume.pdf (of the guest)
- Provide photo.png (of the guest) - needs to end with photo.png

Then:

```bash
python cli.py
```

This will run & open the CLI interface. I recommend going into full-screen terminal mode before running this.

In the CLI interface:
CLI interface:

- list (see all the blogs found in your Zoom folder)
- get <blog_name> (get the blog with the given name, this will be your 'working blog')
- generate all (generate all the attributes for the blog)
- edit <attribute> <value> (edit the attribute with the given value)
- publish (publish the blog to notion)
- reset all (reset all the attributes for the blog) - (NOT YET IMPLEMENTED)
- reset <attribute> (reset the attribute with the given value) - (NOT YET IMPLEMENTED)
