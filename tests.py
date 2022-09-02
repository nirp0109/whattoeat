import pytesseract
from PIL import Image, ImageFilter, ImageDraw
import os, zipfile
import math

CONTOUR_THRESHOLD = 510


def main():
    print(pytesseract.image_to_string(Image.open('G:\\download\\tests\\test.png')))

    # In order to bypass the image conversions of pytesseract, just use relative or absolute image path
    # NOTE: In this case you should provide tesseract supported images or tesseract will return error
    print(pytesseract.image_to_string('G:\\download\\tests\\test.png'))

    # List of available languages
    print(pytesseract.get_languages(config=''))


    # Batch processing with a single file containing the list of multiple image file paths
    # print(pytesseract.image_to_string('G:\\download\\tests\\images.txt'))

    # Timeout/terminate the tesseract job after a period of time
    try:
        print(pytesseract.image_to_string('G:\\download\\tests\\test.jpg', timeout=2))  # Timeout after 2 seconds
        print(pytesseract.image_to_string('G:\\download\\tests\\test.jpg', timeout=0.5))  # Timeout after half a second
    except RuntimeError as timeout_error:
        # Tesseract processing is terminated
        pass

    # Get bounding box estimates
    print('bounding boxes')
    print(pytesseract.image_to_boxes(Image.open('G:\\download\\tests\\test.png')))

    # Get verbose data including boxes, confidences, line and page numbers
    print('verbose data')
    result_list = pytesseract.image_to_data(Image.open('G:\\download\\tests\\test.png'), output_type=pytesseract.Output.DATAFRAME)
    print(type(result_list))
    print(result_list.head().to_string())

    # Get information about orientation and script detection
    print('orientation and script detection')
    print(pytesseract.image_to_osd(Image.open('G:\\download\\tests\\test.png')))

    # Get a searchable PDF
    pdf = pytesseract.image_to_pdf_or_hocr('G:\\download\\tests\\test.png', extension='pdf')
    with open('test.pdf', 'w+b') as f:
        f.write(pdf)  # pdf type is bytes by default

    # Get HOCR output
    print('hocr')
    hocr = pytesseract.image_to_pdf_or_hocr('G:\\download\\tests\\test.png', extension='hocr')
    print(hocr)

    # Get ALTO XML output
    print('alto')
    xml = pytesseract.image_to_alto_xml('G:\\download\\tests\\test.png')
    print(xml)

def test_images_in_zip():
    #  read all images in zip file
    # extract text from images in zip file
    for file in os.listdir('IL_7290002700005_7290112341723_1561354531096.images'):
        if file.endswith(".zip"):
            #   extract zip file
            with zipfile.ZipFile('IL_7290002700005_7290112341723_1561354531096.images/' + file, 'r') as zip_ref:
                zip_ref.extractall('IL_7290002700005_7290112341723_1561354531096_images/')
                # iterate on all extract images from zip
                images_path = 'IL_7290002700005_7290112341723_1561354531096_images/'
                for image in os.listdir(images_path):
                    if image.endswith(".jpg"):
                        # delete background of image and save it, use contour detection to get better results
                        image_path = images_path + image
                        image = Image.open(image_path)
                        image = image.crop((0, 0, image.size[0], image.size[1]))
                        image = image.filter(ImageFilter.CONTOUR)

                        image.save(image_path)
                        # get text from image
                        text = pytesseract.image_to_string(image_path, lang='heb+eng+arb')
                        print(text)
                        print('----------------------------------------------------')



# How to find out the curve of the cylinder in the image
def find_curve():
    # find the cycylinder contour in the image
    image = Image.open('C:\\Users\\user\\PycharmProjects\\whattoeat\\IL_7290002700005_7290112341723_1561354531096_images\\7290112341723_2.jpg')
    image = image.crop((0, 0, image.size[0], image.size[1]))
    image = image.filter(ImageFilter.CONTOUR)
    image.show()
    find_close_shapes_in_image(image)
    # find upper and lower points of the contour
    contours = pytesseract.image_to_data(image, output_type=pytesseract.Output.DATAFRAME)
    print(contours.head().to_string())
    # get image dimensions
    width, height = image.size
    # get image matrix
    pixels = image.load()
    image.show()




    # # get top and bottom points of the matrix where there is a black pixel and background is white
    # top = height +10
    # bottom = 0

    # transform_image_from_polar_to_stright(image)
    #
    # for i in range(height):
    #     for j in range(width):
    #         if sum(pixels[j, i]) < 255:
    #             top = min(i, top)
    #         if sum(pixels[j, height - i - 1]) < 255:
    #             bottom = max(height - i - 1, bottom)
    #     if top < height and bottom > 0:
    #         print('maximum steps: ', i, 'height: ', height)
    #         break
    #
    # # get left and right points of the matrix where there is a black pixel and background is white
    # left = width + 10
    # right = 0
    # for i in range(width):
    #     for j in range(height):
    #         if sum(pixels[i, j]) < 255:
    #             left = min(i, left)
    #         if sum(pixels[width - i - 1, j]) < 255:
    #             right = max(width - i - 1, right)
    #     if left < width and right > 0:
    #         break
    #
    # print("top: " + str(top), "bottom: " + str(bottom))
    # # draw red lines on the image
    # draw = ImageDraw.Draw(image)
    # draw.line((0, top, width, top), fill=(255, 0, 0))
    # draw.line((0, bottom, width, bottom), fill=(255, 0, 0))
    # draw.line((left, 0, left, height), fill=(255, 0, 0))
    # draw.line((right, 0, right, height), fill=(255, 0, 0))
    #
    # image.show()



def transform_image_from_polar_to_stright(image):
    size = image.size
    width, height = size
    # get image matrix
    new_image = Image.new('RGB', (2 * width, height))
    new_pixels = new_image.load()
    pixels = image.load()
    for y in range(height):
        for x in range(width):
            # get polar coordinates
            r = math.sqrt(x ** 2 + y ** 2)
            theta = math.atan2(y, x)
            # get stright coordinates
            x_new = r * math.cos(theta)
            y_new = r * math.sin(theta)
            # set new pixel value
            new_pixels[x, y] = pixels[int(x_new), int(y_new)]

    new_image.show()


def get_adjacent_pixels(pixels, start_point):
    """
    get adjacent pixels to the start point
    :param pixels: image matrix
    :param start_point: start point of the contour
    :return: list of adjacent pixels
    """
    #  find the first dark pixel near the start point where the favor direction list is up, right, down, left
    favor_direction = ['up', 'upright', 'right', 'rightdown', 'down', 'downleft', 'left', 'leftup']
    x, y = start_point
    # get start point value
    start_value = sum(pixels[x, y])
    # get list of adjacent pixels
    adjacent_pixels = []
    for i in range(4):
        # get adjacent pixel coordinates
        x_new, y_new = x, y
        if favor_direction[i] == 'up':
            y_new = y - 1
        elif favor_direction[i] == 'right':
            x_new = x + 1
        elif favor_direction[i] == 'down':
            y_new = y + 1
        elif favor_direction[i] == 'left':
            x_new = x - 1
        elif favor_direction[i] == 'upright':
            x_new = x + 1
            y_new = y - 1
        elif favor_direction[i] == 'rightdown':
            x_new = x + 1
            y_new = y + 1
        elif favor_direction[i] == 'downleft':
            x_new = x - 1
            y_new = y + 1
        elif favor_direction[i] == 'leftup':
            x_new = x - 1
            y_new = y - 1
        # get adjacent pixel value
        adjacent_value = sum(pixels[x_new, y_new])
        # if adjacent pixel is dark and not the start point
        if adjacent_value < CONTOUR_THRESHOLD:
            adjacent_pixels.append((x_new, y_new))

    return adjacent_pixels




def find_close_shapes_in_image(image):
# get image matrix
    pixels = image.load()
    # get image dimensions
    width, height = image.size
    # get top and bottom points of the matrix where there is a black pixel and background is white
    top = height + 10
    bottom = 0
    for i in range(height):
        for j in range(width):
            if sum(pixels[j, i]) < 255:
                top = min(i, top)
            if sum(pixels[j, height - i - 1]) < 255:
                bottom = max(height - i - 1, bottom)
        if top < height and bottom > 0:
            break

    # get left and right points of the matrix where there is a black pixel and background is white
    left = width + 10
    right = 0
    for i in range(width):
        for j in range(height):
            if sum(pixels[i, j]) < 255:
                left = min(i, left)
            if sum(pixels[width - i - 1, j]) < 255:
                right = max(width - i - 1, right)
        if left < width and right > 0:
            break

    print("top: " + str(top), "bottom: " + str(bottom))
    print("left: " + str(left), "right: " + str(right))
    close_shapes = []
    # follow adjacent pixels until there is a white pixel or reach the start point
    # if reach the star point add it to the list of close shapes
    # follow pixels clockwise manner
    draw = ImageDraw.Draw(image)
    for i in range(left, right):
        for j in range(top, bottom):
            if sum(pixels[i, j]) < CONTOUR_THRESHOLD:
                # find all adjacent pixels that are no white and reach the start point
                start_point = (i, j)
                shape = []
                shape.append(start_point)
                next_point = start_point
                found_shape = False
                while True:
                    # get adjacent pixels
                    draw.point(next_point, fill=(255, 0, 0))

                    adjacent_pixels = get_adjacent_pixels(pixels, next_point)
                    # if there is no adjacent pixel break the loop
                    if len(adjacent_pixels) == 0:
                        print("shape: " + str(shape))
                        found_shape = False
                        break
                    # get the first adjacent pixel
                    next_point = adjacent_pixels[0]

                    if not (next_point in shape):
                        shape.append(next_point)
                    else:
                        adjacent_pixels_set = set(adjacent_pixels)
                        shape_set = set(shape)
                        diff = adjacent_pixels_set.difference(shape_set)
                        if len(diff) == 0:
                            found_shape = False
                            print("shape: " + str(shape))
                            break
                        else:
                            next_point = list(diff)[0]
                            shape.append(next_point)

                    if next_point == start_point:
                        found_shape = True
                        print("shape: " + str(shape))
                        break
                if found_shape:
                    close_shapes.append(shape)
    print(close_shapes)
    image.show()
    return close_shapes


def convert_image_to_pdf(image_file_name, pdf_file_name):
    """
    Convert Image to PDF using tsereact
    :param image:
    :param pdf_file_name:
    :return:
    """
    pdf = pytesseract.image_to_pdf_or_hocr(image_file_name, extension='pdf')
    with open(pdf_file_name, 'wb') as f:
        f.write(pdf)


if __name__ == '__main__':
    # test_images_in_zip()
    # main()
    # find_curve()
    convert_image_to_pdf(r"C:\Users\user\Documents\nir\newbornInage.png", r"C:\Users\user\Documents\nir\newbornInage.pdf")
    