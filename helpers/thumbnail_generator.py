import io
import time
from typing import List
from schemas.file import Blog, Thumbnails, ThumbnailParams, ThumbnailResume

from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from pydantic import BaseModel
from gradio_client import Client, handle_file

# Class to generate the thumbnails
class ThumbnailGenerator:
    """
    Class to generate the thumbnails
    """

    def __init__(self):
        """
        Initialize the ThumbnailGenerator
        """
        pass

    def generate_thumbnails(self, file: Blog):
        """
        Generate the thumbnails for the given blog
        """
        photo_no_bg = self.remove_bg(file)

        universities_text_height = int(self.calculate_text_height(file.thumbnails.thumbnail_text.universities, self.get_font("university", 74)))

        if file.thumbnails and file.thumbnails.landscape_params:
            landscape_params = file.thumbnails.landscape_params
        else:
            landscape_params = ThumbnailParams(
                height=1200, width=1680, 
                companies_font_size=145, companies_x_offset=64, companies_y_offset=53, 
                universities_x_offset=64, universities_y_offset=1200 - universities_text_height - 60, 
                portrait_ratio=0.9, portrait_align="right"
            )
        landscape = self.generate_thumbnail(file.thumbnails.thumbnail_text, photo_no_bg, landscape_params)

        companies_text_height = int(self.calculate_text_height(file.thumbnails.thumbnail_text.companies, self.get_font("company", 99)))
        
        if file.thumbnails and file.thumbnails.square_params:
            square_params = file.thumbnails.square_params
        else:
            square_params = ThumbnailParams(
                height=1080, width=1080,
                companies_font_size=99, companies_x_offset=14, companies_y_offset=18,
                universities_x_offset=14, universities_y_offset=companies_text_height + 60,
                portrait_ratio=0.8, portrait_align="center"
            )
        square = self.generate_thumbnail(file.thumbnails.thumbnail_text, photo_no_bg, square_params)

        return Thumbnails(
            thumbnail_text=file.thumbnails.thumbnail_text,
            photo_no_bg=self.image_to_bytes(photo_no_bg),
            landscape=self.image_to_bytes(landscape),
            square=self.image_to_bytes(square),
            landscape_params=landscape_params,
            square_params=square_params
        )
        
    def generate_thumbnail(self, thumbnail_resume: ThumbnailResume, guest_photo_no_bg: str, params: ThumbnailParams):
        """
        Generate the thumbnail for the given blog, using the provided thumbnail parameters.

        Generates companies, universities, portrait and name overlays, then stitches it together.
        """
        # 1. Generate companies text overlay
        companies_overlay, companies_mask = self.generate_companies_overlay(thumbnail_resume, params)

        # 2. Generate universities text overlay
        universities_overlay, universities_mask = self.generate_universities_overlay(thumbnail_resume, params)

        # 3. Generate portrait with name overlay
        portrait, portrait_gray, name_overlay_position = self.generate_portrait(thumbnail_resume, guest_photo_no_bg, params)

        # 4. Paste everything together and save

        # Companies and universities
        thumbnail = Image.open("assets/bg.png")
        thumbnail = thumbnail.resize((params.width, params.height), Image.LANCZOS)

        thumbnail.paste(companies_mask, (params.companies_x_offset, params.companies_y_offset), companies_overlay)
        thumbnail.paste(universities_overlay, (params.universities_x_offset, params.universities_y_offset), universities_overlay)
        
        # Portrait
        portrait_width, portrait_height = portrait.size

        if params.portrait_align == "right":
            paste_x = params.width - portrait_width + params.portrait_x_offset #Right of thumbnail
        elif params.portrait_align == "center":
            paste_x = ((params.width - portrait_width) // 2) + params.portrait_x_offset #Center of thumbnail

        paste_y = params.height - portrait_height - params.portrait_y_offset #Bottom of thumbnail
        thumbnail.paste(portrait_gray, (paste_x, paste_y), portrait)

        # Name + Arrow
        name_overlay = self.generate_name_overlay(thumbnail_resume, params)
        name_overlay_position = (name_overlay_position[0] + params.name_x_offset + paste_x, name_overlay_position[1] - params.name_y_offset + paste_y)
        thumbnail.paste(name_overlay, name_overlay_position, name_overlay)

        return thumbnail

    # Thumbnail generation
    # 1. Generate companies text overlay
    def generate_companies_overlay(self, thumbnail_resume: ThumbnailResume, params: ThumbnailParams):
        """
        Generates the companies text overlay for the thumbnail
        """
        # Load the white gradient mask (ensure it's RGBA or RGB)
        gradient_mask = Image.open('assets/white_gradient_mask.png').convert('RGBA')
        # Resize gradient to match text overlay size
        gradient_mask = gradient_mask.resize((params.width, params.height), Image.LANCZOS)

        # Create a new RGBA image for the text overlay
        text_overlay = Image.new('RGBA', (params.width, params.height), (0, 0, 0, 0))

        # Get the font
        font = self.get_font("company", params.companies_font_size)

        # Create a mask for the text (this will be the shape of the text)
        text_mask = Image.new('L', (params.width, params.height), 0)  # L mode for grayscale (mask)
        text_draw = ImageDraw.Draw(text_mask)
        
        # Draw the text in white on the text_mask
        spacing = font.size * 0.21
        text_draw.text((0, 0), '\n'.join(thumbnail_resume.companies), font=font, fill=255, spacing=spacing)  # White text as a mask

        # Now, composite the gradient with the text mask
        gradient_filled_text = Image.composite(gradient_mask, text_overlay, text_mask).convert('RGBA')

        return gradient_filled_text, text_mask
    
    # 2. Generate universities text overlay
    def generate_universities_overlay(self, thumbnail_resume: ThumbnailResume, params: ThumbnailParams, debug = False):
        """
        Generates the universities text overlay for the thumbnail
        """
        uni_text = '\n'.join(thumbnail_resume.universities)

        font = self.get_font("university", params.universities_font_size)
        text_height = self.calculate_text_height(thumbnail_resume.universities, font)

        # Calculate text width
        text_width = max(font.getbbox(university)[2] - font.getbbox(university)[0] for university in thumbnail_resume.universities)

        overlay_width = int(text_width)
        overlay_height = int(text_height)

        # Create an RGBA image to write the text, sized to the calculated dimensions
        colour = (255, 255, 255, 255) if debug else (0, 0, 0, 0)
        text_overlay = Image.new('RGBA', (overlay_width, overlay_height), colour)

        # Draw the text in hex(38, 38, 38) on the text_overlay
        draw = ImageDraw.Draw(text_overlay)
        spacing = font.size * 0.21
        draw.text((0, 0), uni_text, font=font, fill=(38, 38, 38, 255), spacing=spacing)
        
        # Create a mask for the text
        text_mask = text_overlay.convert('L')

        return text_overlay, text_mask

    # 3. Generate portrait with name overlay
    def generate_portrait(self, thumbnail_resume: ThumbnailResume, guest_photo_no_bg: str, params: ThumbnailParams):
        """
        Generates the portrait for the thumbnail
        """
        # Load the images
        portrait = guest_photo_no_bg
        portrait = portrait.crop(portrait.getbbox())
        grayscale = portrait.convert('L')
        
        # Resize the portrait to 2/3 of height while maintaining the aspect ratio
        height = int(params.portrait_ratio * params.height)
        width = int(portrait.width * height / portrait.height)
        portrait = portrait.resize((width, height), Image.LANCZOS)
        grayscale = grayscale.resize((width, height), Image.LANCZOS)

        # Increase the contrast and brightness of the grayscale image
        # contrast_enhancer = ImageEnhance.Contrast(grayscale)
        # grayscale = contrast_enhancer.enhance(1.5)

        # Increase the brightness (exposure)
        # brightness_enhancer = ImageEnhance.Brightness(grayscale)
        # grayscale = brightness_enhancer.enhance(1.2)  # Slight increase in brightness

        # Paste the "scanlines_mask.png" onto grayscale
        scanlines_mask = Image.open('assets/scanlines_mask.png')
        max_dimension = max(grayscale.width, grayscale.height)
        scanlines_mask = scanlines_mask.resize((max_dimension, max_dimension), Image.LANCZOS)
        grayscale.paste(scanlines_mask, (0, 0), scanlines_mask)

        # Check for transparent areas
        width, height = portrait.size
        transparent_areas = []
        for y in range(height):
            for x in range(width):
                if portrait.getpixel((x, y))[3] == 0:  # Check alpha channel
                    transparent_areas.append((x, y))
        
        # Split the portrait into 4 quadrants
        width, height = portrait.size
        mid_x, mid_y = width // 2, height // 2
        
        # Focus on the top right quadrant
        top_right_transparent = [
            (x, y) for x, y in transparent_areas
            if x >= mid_x and y < mid_y
        ]
        
        if top_right_transparent:
            # Calculate the center of the transparent area in the top right quadrant
            center_x = sum(x for x, _ in top_right_transparent) // len(top_right_transparent)
            center_y = sum(y for _, y in top_right_transparent) // len(top_right_transparent)
                        
            # Create the name overlay
            name_overlay = self.generate_name_overlay(thumbnail_resume, params)
            
            # Calculate the position to center the name_overlay on the transparent area
            overlay_x = center_x - name_overlay.width // 2 
            overlay_y = center_y - name_overlay.height // 2 
            
            # Ensure the overlay stays within the portrait bounds
            overlay_x = max(0, min(overlay_x, width - name_overlay.width))
            overlay_y = max(0, min(overlay_y, height - name_overlay.height))
            
            name_overlay_position = (overlay_x, overlay_y)
        else:
            name_overlay_position = (0, 0)
            print("No transparent areas found in the top right quadrant.")

        # Return name_overlay_position so we can paste it onto thumbnail (to avoid portrait cropping when manually adjusting name x,y offset)
        return portrait, grayscale, name_overlay_position
    
    # 4. Generate name overlay
    def generate_name_overlay(self, thumbnail_resume: ThumbnailResume, params: ThumbnailParams, debug = False):
        """
        Generates the name overlay for the thumbnail
        """
        font = self.get_font("name", params.name_font_size)
        
        # Get the size of the text using getbbox()
        bbox = font.getbbox(thumbnail_resume.first_name)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Open and resize the arrow image
        arrow = Image.open('assets/arrow_1.png')
        arrow_width, arrow_height = arrow.size
        arrow_aspect_ratio = arrow_width / arrow_height
        new_arrow_height = 150
        new_arrow_width = int(new_arrow_height * arrow_aspect_ratio)
        arrow = arrow.resize((new_arrow_width, new_arrow_height), Image.LANCZOS)

        # Create the frame based on the bounding box of the text and arrow
        gap = 40
        image_width = max(text_width, new_arrow_width) + 20  # Add some padding
        image_height = text_height + new_arrow_height + gap + 20  # Add some padding

        colour = (255, 255, 255, 255) if debug else (0, 0, 0, 0)
        image = Image.new('RGBA', (image_width, image_height), colour)
        draw = ImageDraw.Draw(image)

        # Calculate positions for text and arrow
        text_x = (image_width - text_width) // 2
        text_y = 10  # Top padding
        arrow_x = (image_width - new_arrow_width) // 2
        arrow_y = text_y + text_height + gap  # 10 pixels gap between text and arrow

        # Draw the text and paste the arrow
        fill = (0, 0, 0, 255) if debug else (255, 255, 255, 255)
        draw.text((text_x, text_y), thumbnail_resume.first_name, font=font, fill=fill)
        image.paste(arrow, (arrow_x, arrow_y), arrow)

        return image

    # === Helper functions ===
    # Background removal    
    def remove_bg(self, file: Blog, debug=False):
        """
        Remove the background from the given photo using a HuggingFace BG removal model.
        """
        if debug:
            return Image.open(file.files.photo).convert("RGBA")

        # If existing bg_removed photo, check if it matches the current photo otherwise remove background for the current photo
        if file.thumbnails and file.thumbnails.photo_no_bg:
            # TODO: Add support to auto-remove background if the photo has changed
            return Image.open(io.BytesIO(file.thumbnails.photo_no_bg))
        
        client = Client("ZhengPeng7/BiRefNet_demo")
        result = client.predict(
            images=handle_file(file.files.photo),
            resolution="1024x1024",
            weights_file="General",
            api_name="/image"
        )

        return Image.open(result[0])
        
    def calculate_text_height(self, texts: List[str], font: ImageFont.FreeTypeFont):
        """
        Calculate the height of a block of text with the given font (to calculate positioning of overlays)
        """
        # Calculate the height of the text
        ascent, descent = font.getmetrics()
        (width, baseline), (offset_x, offset_y) = font.font.getsize(texts[0])
        
        line_height = ascent + descent - offset_y

        # Calculate total text height including line spacing
        line_spacing = font.size * 0.21  # You can adjust this value
        text_height = line_height * len(texts) + line_spacing * (len(texts) - 1)

        return text_height

    def get_font(self, font_name: str, font_size: int):
        """
        Gets the font for the given font name and size with the specified style.
        """
        fonts = {
            "company": ImageFont.truetype("/Users/anirudhh/Library/Fonts/Inter-VariableFont_opsz,wght.ttf", font_size),
            "university": ImageFont.truetype("/Users/anirudhh/Library/Fonts/JetBrainsMono-VariableFont_wght.ttf", font_size),
            "name": ImageFont.truetype("/Users/anirudhh/Library/Fonts/LondrinaSolid-Regular.ttf", font_size)
        }

        selected_font = fonts[font_name]

        if font_name == "company":
            selected_font.set_variation_by_name("Bold")
        elif font_name == "university":
            selected_font.set_variation_by_name("Regular")

        return selected_font

    def image_to_bytes(self, img: Image.Image, format: str = 'PNG') -> bytes:
        """
        Convert an image to bytes
        """
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format=format)
        return img_byte_arr.getvalue()