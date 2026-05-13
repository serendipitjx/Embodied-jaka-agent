import cv2
from pyzbar import pyzbar

def decode_qr(path):
    img = cv2.imread(path)
    if img is None:
        print(f"无法打开图片: {path}")
        return

    barcodes = pyzbar.decode(img)
    if not barcodes:
        print("未识别到二维码或条码")
        return

    for barcode in barcodes:
        data = barcode.data.decode("utf-8")
        print(data)

if __name__ == "__main__":
    path = "1.png"
    decode_qr(path)
