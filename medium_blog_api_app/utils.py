## validate images size and type(jpg, png, jpeg)
from django.forms import ValidationError

def validate_image(image):
    allowed_extensions = ['jpg', 'png', 'jpeg']
    image_extension = image.name.split('.')[-1].lower()
    if image_extension not in allowed_extensions:
        raise ValidationError(f"Invalid image format. Allowed formats: {', '.join(allowed_extensions)}")
    
    if image.size > 2 * 1024 * 1024:
        raise ValidationError("Image size should not exceed 2MB.")