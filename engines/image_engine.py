from PIL import Image

def convert_image(input_path, output_path):

    image = Image.open(input_path)

    image.convert("RGB").save(output_path)