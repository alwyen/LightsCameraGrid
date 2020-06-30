import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy import interpolate
import scipy.signal as ss

# img_path = r'C:\Users\alexy\OneDrive\Documents\STIMA\Images\BRF_images\ecosmart_CFL_14w.jpg' #cfl_1
img_path = r'C:\Users\alexy\OneDrive\Documents\STIMA\Images\BRF_images\maxlite_CFL_15w.jpg' #cfl_1
# img_path = r'C:\Users\alexy\OneDrive\Documents\STIMA\Images\BRF_images\ge_incandescant_25w.jpg' #incandescent_1
# img_path = r'C:\Users\alexy\OneDrive\Documents\STIMA\Images\BRF_images\philips_incandescent_40w.jpg' #incandescent_2
# img_path = r'C:\Users\alexy\OneDrive\Documents\STIMA\Images\BRF_images\paper_1.jpg'
height = 576
width = 1024

def img_from_path(img_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    # img = cv2.resize(img, (width, height))
    return img

def show_plot(array):
    plt.plot(array)
    plt.show()

def show_image(img):
    cv2.imshow('img', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def brf_extraction(img):
    height = img.shape[0]
    width = img.shape[1]
    column = img[0:height,int(width/2)]
    # column = img[0:height,1239]
    return column

def upper_envelope(brf):
    brf = np.array(brf)

    peak_indices = ss.find_peaks(brf)[0]
    peak_values = brf[peak_indices]
    upper_model = interpolate.interp1d(peak_indices, peak_values, fill_value='extrapolate')
    upper_envelope_values = np.zeros(len(brf))
    upper_envelope_values[peak_indices] = peak_values
    upper_envelope = upper_model(np.arange(0, len(brf), 1))

    return upper_envelope

def lower_envelope(brf):
    brf = np.array(brf)

    trough_indices = ss.find_peaks(-brf)[0]
    trough_values = brf[trough_indices]
    lower_model = interpolate.interp1d(trough_indices, trough_values, fill_value='extrapolate')
    lower_envelope_values = np.zeros(len(brf))
    lower_envelope_values[trough_indices] = trough_values
    lower_envelope = lower_model(np.arange(0, len(brf), 1))

    return lower_envelope

def upper_lower_envelope_mean(upper_envelope, lower_envelope):
    processed_envelope = (upper_envelope + lower_envelope)/2
    return processed_envelope

def moving_average(image_column, window_size):
    average = []
    for x in range(len(image_column)-window_size):
        average.append(np.sum(image_column[x:x+window_size])/window_size/255)
    return average

def crop_brf(brf, start_index, end_index):
    return brf[start_index:end_index]

if __name__ == '__main__':
    img = img_from_path(img_path)
    brf = brf_extraction(img)
    brf = crop_brf(brf, 0, 250)

    brf = crop_brf(brf, 0, 500)
    upper_envelope = upper_envelope(brf)
    lower_envelope = lower_envelope(brf)
    processed_brf = upper_lower_envelope_mean(upper_envelope, lower_envelope)
    show_plot(processed_brf)
    brf_average = moving_average(processed_brf, 5)
    show_plot(brf_average)
    # brf = envelope_processing(brf)
    # envelope_processing(brf_average)
    # show_plot(brf)