# Import all necessary packages
import numpy as np
from matplotlib import pyplot as plt
import cv2
import glob
import copy
import skimage.filters
import skimage.exposure
import skimage.filters.rank
import skimage.morphology
import scipy.ndimage
import os
import matplotlib.image as img
from skimage.feature import hessian_matrix, hessian_matrix_eigvals
from skimage.filters import hessian
from skimage import morphology
from skimage.filters import threshold_otsu, rank
from skimage.morphology import disk
import pywt


# Define Functions
def threshold(img,k):
    ret = copy.deepcopy(img)
    ret[ret<k] = 0
    ret[ret>=k] = 255
    return ret

def GlobalOtsu(img):
    foreground = img[img>=0]
    background = img[img<0]
    
    final_var = (np.var(foreground) * len(foreground) + np.var(background) * len(background))/(len(foreground) + len(background))
    if(np.isnan(final_var)):
        final_var = -1
        
    final_thresh = 0
    for i in np.linspace(np.min(img), np.max(img), num=255):
        foreground = img[img>=i]
        background = img[img<i]
        var = (np.var(foreground) * len(foreground) + np.var(background) * len(background))/(len(foreground) + len(background))
        
        if(np.isnan(var)):
            var = -1
            
        if(var!=-1 and (var<final_var or final_var ==-1)):
            final_var = var
            final_thresh = i
    return threshold(img,final_thresh)
# The function GlobalOtsu performs Global Otsu Thresholding on the Enhanced Thick Vessel Image
# before fusion with the Thin vessel image to give the final
def AreaThreshold(img, area = 5):
    nlabels,labels,stats,centroid = cv2.connectedComponentsWithStats(np.uint8(img), 4, cv2.CV_32S)

    output = np.copy(img)
    
    for i in range(output.shape[0]):
        for j in range(output.shape[1]):
            if stats[labels[i][j], cv2.CC_STAT_AREA] < area:
                output[i][j] = 0
                
    return output

def LocalOtsu1(img,radius = 5):
    selem = disk(radius)
    local_otsu = rank.otsu(img, selem)
    output = np.copy(img)
    output[output < local_otsu] = 0
    output[output >= local_otsu] = 255
    return output

def LocalOtsu2(img,radius = 15):
    selem = disk(radius)
    local_otsu = rank.otsu(img, selem)
    output = np.copy(img)
    rng = local_otsu.max() - local_otsu.min()
    mid = rng/2 + local_otsu.min()
    local_otsu[local_otsu<mid] = mid
    output[output < local_otsu] = 0
    return output

def AccuracyMetrics(img,imggt):
    matches = np.copy(img[img==imggt])
    mismatches = np.copy(img[img!=imggt])
    TP = sum(matches==255)
    TN = sum(matches==0)
    FP = sum(mismatches==255)
    FN = sum(mismatches==0)
#     print(matches.shape)
#     print(mismatches.shape)
#     print("TP ",TP)
#     print("TN ",TN)
#     print("FP ",FP)
#     print("FN ",FN)
    Acc = (TP+TN)/(TP+TN+FP+FN)
    Sn = TP/(TP+FN)
    Sp = TN/(TN+FP)
    Auc = (Sn+Sp)/2
    return Acc,Sn,Sp,Auc

#using wavelet method for image fusion
def image_fusion(img1,img2):
    w1 = pywt.wavedec2(img1, 'db1')
    w2 = pywt.wavedec2(img2, 'db1')
    elem = (w1[0]+w2[0])/2
    fw = [elem]
    for i in range(len(w1)-1):
        x,y,z = (w1[i+1][0] + w2[i+1][0])/2, (w1[i+1][1] + w2[i+1][1])/2, (w1[i+1][2] + w2[i+1][2])/2
        fw.append((x,y,z))
    output = pywt.waverec2(fw, 'db1')
    amin = np.min(output)
    amax = np.max(output)
    output = 255* ((output - amin)/(amax-amin))
    output = cv2.resize(output,img1.T.shape)
    return output
#Image fusion of the Think Vesel and Otsu Global Thresholded Thick Vessel image is done to define both Thin and Thick vessels after Thresholding



def Segment(ur):
    print(f"URL IS: {ur}")
    #Obtain image
    # url = "../dataset/im0319.ppm"
    url = ur
    img = cv2.imread(url)
    img = cv2.cvtColor(img,cv2.COLOR_BGR2RGB)

    #Split into 3 channels
    imgR = img[:,:,0]
    imgG = img[:,:,1]
    imgB = img[:,:,2]

    #Pre-processing

        #CLAHE
    clipLimit = 3
    clahe = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=(8,8))
    clahe_img = clahe.apply(imgG)
    print("CLAHE")
        #Morphological Filters
    retinal_disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(9,9))
    Topen = cv2.morphologyEx(clahe_img,cv2.MORPH_OPEN,retinal_disc)
    Tclose = cv2.morphologyEx(Topen, cv2.MORPH_CLOSE, retinal_disc)
    TopHat = (clahe_img - Tclose)
    print("TOP HAT")
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(2,2))
    min_image = cv2.erode(TopHat, kernel)
    min_image = cv2.dilate(min_image, kernel)

    #Implementation
        #Obtain Thin Vessels
    HessThin = hessian_matrix(min_image, sigma=1.2, order='rc')
    EignThin = hessian_matrix_eigvals(HessThin) [1]
        #Obtain Thick Vessels
    HessWide = hessian_matrix(min_image, sigma=4, order='rc')
    EignWide = hessian_matrix_eigvals(HessWide) [1]
    #Eigenvalues of the Hessian Matrix of the Green Channel Image are taken with various Sigma values to give both Thick and Thin vessel enhanced images
    print("HESSIAN")
        #Global Otsu Thresholding
    val1 = GlobalOtsu(1-EignWide)

            #Normalisation
    thinN = cv2.normalize(1-EignThin,  None, 0, 255, cv2.NORM_MINMAX)
    val1 = cv2.normalize(val1,  None, 0, 80, cv2.NORM_MINMAX)
        #Image Fusion

    imgFuse = image_fusion(val1,thinN)
    print("FUSION")
        #Local Otsu Thresholding
    lOtsu = LocalOtsu2(imgFuse.astype('uint8'))
        #Area Thresholding
    out = AreaThreshold(lOtsu,50)
    out[out!=0] = 255
    print("LOCAL AND AREA")
    #Reference Image 
    urlRef = "testing/labels-ah/"+url[-10:-3]+"ah.ppm"
    Acc1 = -1
    Sn1  = -1
    Sp1  = -1
    Auc1 = -1
    if os.path.exists(urlRef):
        imgRef = cv2.imread(urlRef)
        imgRef = imgRef[:,:,1]
        # fig = plt.figure()
        # fig.add_subplot(1, 2, 1)
        # plt.imshow(out,cmap='gray')
        # plt.title('Output')
        # fig.add_subplot(1, 2, 2)
        # plt.imshow(imgRef,cmap='gray')
        # plt.title('Reference Image')
        # plt.show()

        print("All Done")
        #Performance criteria
        Acc1,Sn1,Sp1,Auc1 = AccuracyMetrics(out,imgRef)
        #AccuracyMetrics is a function used to check how accurate the Vessem images in the Dataset are to our acquired output

        print(f"Accuracy Value for segmenation is {Acc1}")
        print(f"Sensitivity for segmenation is {Sn1}")
        print(f"Specificity for segmenation is {Sp1}")
        print(f"Receiver Operating Characteristic for segmenation is {Auc1}")
    return out,Acc1,Sn1,Sp1,Auc1
# main()
