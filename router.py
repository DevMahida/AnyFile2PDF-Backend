from engines.image_engine import convert_image
from engines.csv_engine import convert_csv
from engines.docx_engine import convert_docx
from engines.ipynb_engine import convert_ipynb


def route_conversion(input_path, output_path):

    extension = input_path.split(".")[-1].lower()

    if extension in ["png", "jpg", "jpeg"]:
        convert_image(input_path, output_path)

    elif extension == "csv":
        convert_csv(input_path, output_path)

    elif extension in ["docx", "pptx", "xlsx"]:
        convert_docx(input_path, output_path)

    elif extension == "ipynb":
        convert_ipynb(input_path, output_path)

    else:
        raise Exception("Unsupported file format")