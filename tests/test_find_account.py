# capture_and_ocr_hwnd.py
import ctypes, time, re
import win32gui, win32ui, win32con
from PIL import Image, ImageFilter, ImageOps
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"  # 필요시 수정
target_hwnd = 0x10d58
ACCOUNT_RE = re.compile(r'\b\d{4}-\d{4}-\d{2}\b')

def rect_of(hwnd):
    try:
        return win32gui.GetWindowRect(hwnd)
    except:
        return (0,0,0,0)

def pil_from_bitmap(hdc_src, x, y, w, h):
    memdc = win32ui.CreateDCFromHandle(hdc_src)
    compat = memdc.CreateCompatibleDC()
    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(memdc, w, h)
    compat.SelectObject(bmp)
    compat.BitBlt((0,0),(w,h), memdc, (x,y), win32con.SRCCOPY)
    bmpinfo = bmp.GetInfo()
    bmpstr = bmp.GetBitmapBits(True)
    img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
    try: compat.DeleteDC()
    except: pass
    try: memdc.DeleteDC()
    except: pass
    try: win32gui.DeleteObject(bmp.GetHandle())
    except: pass
    return img

def capture_bitblt(rect):
    l,t,r,b = rect
    w,h = r-l, b-t
    if w<=0 or h<=0: return None
    hdesktop = win32gui.GetDesktopWindow()
    hdc = win32gui.GetWindowDC(hdesktop)
    try:
        return pil_from_bitmap(hdc, l, t, w, h)
    finally:
        try: win32gui.ReleaseDC(hdesktop, hdc)
        except: pass

def capture_printwindow(hwnd, rect):
    l,t,r,b = rect
    w,h = r-l, b-t
    if w<=0 or h<=0: return None
    PW_RENDERFULLCONTENT = 0x00000002
    hdc = win32gui.GetWindowDC(hwnd)
    try:
        srcdc = win32ui.CreateDCFromHandle(hdc)
        memdc = srcdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, w, h)
        memdc.SelectObject(bmp)
        res = ctypes.windll.user32.PrintWindow(hwnd, memdc.GetSafeHdc(), PW_RENDERFULLCONTENT)
        bmpinfo = bmp.GetInfo(); bmpstr = bmp.GetBitmapBits(True)
        img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
        try: memdc.DeleteDC()
        except: pass
        try: srcdc.DeleteDC()
        except: pass
        try: win32gui.DeleteObject(bmp.GetHandle())
        except: pass
        return img if res != 0 else None
    finally:
        try: win32gui.ReleaseDC(hwnd, hdc)
        except: pass

def preprocess_for_account(img):
    # convert to grayscale, increase contrast, bilateral-like reduce noise, adaptive threshold
    gray = img.convert('L')
    # resize to improve small text readability
    scale = max(1, int(2000 / max(img.size)))  # tune: aim larger if small
    if scale > 1:
        gray = gray.resize((gray.width*scale, gray.height*scale), Image.LANCZOS)
    # enhance: unsharp + contrast
    gray = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=150, threshold=3))
    gray = ImageOps.autocontrast(gray, cutoff=1)
    # adaptive threshold-ish: use point
    gray = gray.point(lambda p: 0 if p < 180 else 255)
    return gray

def ocr_account_from_image(img):
    if img is None: return None
    proc = preprocess_for_account(img)
    config = '--psm 7 -c tessedit_char_whitelist=0123456789-'
    txt = pytesseract.image_to_string(proc, config=config)
    txt = txt.strip()
    m = ACCOUNT_RE.search(txt)
    return m.group() if m else None

def main():
    rect = rect_of(target_hwnd)
    print("rect:", rect)
    # 1) BitBlt capture of that rect
    img = capture_bitblt(rect)
    acct = ocr_account_from_image(img)
    if acct:
        print("FOUND (BitBlt OCR):", acct); return
    # 2) PrintWindow capture
    print("BitBlt OCR failed or none; trying PrintWindow...")
    img2 = capture_printwindow(target_hwnd, rect)
    acct2 = ocr_account_from_image(img2)
    if acct2:
        print("FOUND (PrintWindow OCR):", acct2); return
    # 3) fallback: full-window PrintWindow (bigger)
    print("PrintWindow OCR failed; trying full window PrintWindow capture...")
    try:
        top_hwnd = win32gui.GetAncestor(target_hwnd, win32con.GA_ROOT)
        full_rect = win32gui.GetWindowRect(top_hwnd)
        img3 = capture_printwindow(top_hwnd, full_rect)
        acct3 = ocr_account_from_image(img3.crop((rect[0]-full_rect[0], rect[1]-full_rect[1], rect[2]-full_rect[0], rect[3]-full_rect[1])))
        if acct3:
            print("FOUND (Full-window PrintWindow OCR):", acct3); return
    except Exception:
        pass
    print("Not found by image OCR.")

if __name__ == '__main__':
    main()