#coding:utf-8
'''
Created on 2014年2月28日
this code is mainly from django-ckeditor Project

@author: hulda
'''
from io import BytesIO
import os.path

try:
    from PIL import Image, ImageOps
except ImportError:
    import Image
    import ImageOps

import mimetypes
import random
import string


from django.template.defaultfilters import slugify
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile


def slugify_filename(filename):
    """ Slugify filename """
    name, ext = os.path.splitext(filename)
    slugified = get_slugified_name(name)
    return slugified + ext


def get_slugified_name(filename):
    slugified = slugify(filename)
    return slugified or get_random_string()


def get_random_string():
    return ''.join(random.sample(string.ascii_lowercase*6, 6))


def get_thumb_filename(file_name):
    """
    Generate thumb filename by adding _thumb to end of
    filename before . (if present)
    """
    return u'{0}_thumb{1}'.format(*os.path.splitext(file_name))

def get_outline_filename(file_name):
    """
    Generate thumb filename by adding _thumb to end of
    filename before . (if present)
    """
    return u'{0}_outline{1}'.format(*os.path.splitext(file_name))

def get_avatar_filename(file_name):
    """
    Generate thumb filename by adding _thumb to end of
    filename before . (if present)
    """
    return u'{0}_avatar{1}'.format(*os.path.splitext(file_name))


def get_image_format(extension):
    mimetypes.init()
    return mimetypes.types_map[extension]


def get_media_url(path):
    """
    Determine system file's media URL.
    """
    return default_storage.url(path)

THUMBNAIL_SIZE = (75, 75)

def image_verify(f):
    Image.open(f).verify()
#
#上面的是utils
#

def create_outline(file_path):
    thumbnail_filename = get_outline_filename(file_path)
    thumbnail_format = get_image_format(os.path.splitext(file_path)[1])
    file_format = thumbnail_format.split('/')[1]

    image = default_storage.open(file_path)
    image = Image.open(image)

    # Convert to RGB if necessary
    # Thanks to Limodou on DjangoSnippets.org
    # http://www.djangosnippets.org/snippets/20/
    if image.mode not in ('L', 'RGB'):
        image = image.convert('RGB')

    # scale and crop to thumbnail
    MAX_SIZE = 360
    width, height = image.size
    if width>MAX_SIZE or height>MAX_SIZE:
        if width>=height:
            height = MAX_SIZE*height/width
            width  = MAX_SIZE
        else:
            width  = MAX_SIZE*width/height
            height = MAX_SIZE
            
    imagefit = ImageOps.fit(image,(width,height), Image.ANTIALIAS)
    thumbnail_io = BytesIO()
    imagefit.save(thumbnail_io, format=file_format)

    thumbnail = InMemoryUploadedFile(
        thumbnail_io,
        None,
        thumbnail_filename,
        thumbnail_format,
        len(thumbnail_io.getvalue()),
        None)
    thumbnail.seek(0)

    return default_storage.save(thumbnail_filename, thumbnail)


def should_create_thumbnail(file_path):
    image = default_storage.open(file_path)
    try:
        Image.open(image)
    except IOError:
        return False
    else:
        return True
    
def crop_avatar(file_path,size):
    
    avatar_format = get_image_format(os.path.splitext(file_path)[1])
    file_format = avatar_format.split('/')[1]
    avatar_filename = get_avatar_filename(file_path)
    
    image_file = default_storage.open(file_path)
    image = Image.open(image_file)
    if image.mode not in ('L', 'RGB'):
        image = image.convert('RGB')
    width,height = image.size
    
    crop_ratio = float(200)/(size[2]-size[0])
    ratio = float(480)/width * crop_ratio
    
    width  = int(width  * ratio)
    height = int(height * ratio)
    
    left = int(size[0] * crop_ratio)
    top =  int(size[1] * crop_ratio)

    crop_image = image.resize((width,height),Image.ANTIALIAS)
    
    
    crop_image = crop_image.crop((left,top,left+200,top+200))
    
    avatar_io = BytesIO()#this is for default_storage using.
    crop_image.save(avatar_io, format=file_format)

    avatar = InMemoryUploadedFile(
        avatar_io,
        None,
        avatar_filename,
        avatar_format,
        len(avatar_io.getvalue()),
        None)
    avatar.seek(0)
    saved_path =  default_storage.save(avatar_filename, avatar)
    image_file.close()
    default_storage.delete(file_path)

    
    return saved_path

def compress_quality(file,filename):
    image = Image.open(file)
    image.save(filename, quality=50, optimize=True)