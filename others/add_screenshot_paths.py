"""
add_screenshot_paths.py
"""
screenshot_dict = '''
SCREENSHOT_PATHS = {
    "login": r"C:\\Users\\mamue\\.gemini\\antigravity\\brain\\f3d6fde2-50db-4e24-b4d1-b9a9f17c89f9\\.user_uploaded\\media_1795064046364_55c6f50b.jpg",
    "dashboard": r"C:\\Users\\mamue\\.gemini\\antigravity\\brain\\f3d6fde2-50db-4e24-b4d1-b9a9f17c89f9\\.user_uploaded\\media_1795064122177_41607fcf.jpg",
    "smart_alerts": r"C:\\Users\\mamue\\.gemini\\antigravity\\brain\\f3d6fde2-50db-4e24-b4d1-b9a9f17c89f9\\.user_uploaded\\media_1795064173592_c3581756.jpg",
    "admin_management": r"C:\\Users\\mamue\\.gemini\\antigravity\\brain\\f3d6fde2-50db-4e24-b4d1-b9a9f17c89f9\\.user_uploaded\\media_1795064197281_d1fdd7f9.jpg",
    "settings": r"C:\\Users\\mamue\\.gemini\\antigravity\\brain\\f3d6fde2-50db-4e24-b4d1-b9a9f17c89f9\\.user_uploaded\\media_1795064232485_a0098e70.jpg",
    "products": r"C:\\Users\\mamue\\.gemini\\antigravity\\brain\\f3d6fde2-50db-4e24-b4d1-b9a9f17c89f9\\.user_uploaded\\media_1795064255720_a5218abf.jpg",
    "categories": r"C:\\Users\\mamue\\.gemini\\antigravity\\brain\\f3d6fde2-50db-4e24-b4d1-b9a9f17c89f9\\.user_uploaded\\media_1795064285678_62c18dab.jpg",
    "stock_in": r"C:\\Users\\mamue\\.gemini\\antigravity\\brain\\f3d6fde2-50db-4e24-b4d1-b9a9f17c89f9\\.user_uploaded\\media_1795064306702_500c19b3.jpg",
    "stock_out": r"C:\\Users\\mamue\\.gemini\\antigravity\\brain\\f3d6fde2-50db-4e24-b4d1-b9a9f17c89f9\\.user_uploaded\\media_1795064330069_62e1602f.jpg",
    "reports": r"C:\\Users\\mamue\\.gemini\\antigravity\\brain\\f3d6fde2-50db-4e24-b4d1-b9a9f17c89f9\\.user_uploaded\\media_1795064353799_649319e3.jpg",
    "otp_verify": r"C:\\Users\\mamue\\.gemini\\antigravity\\brain\\f3d6fde2-50db-4e24-b4d1-b9a9f17c89f9\\.user_uploaded\\media_1795012915165_79dfebb5.jpg",
}
'''

with open('report_content.py', 'a', encoding='utf-8') as f:
    f.write(screenshot_dict)

print("SCREENSHOT_PATHS added successfully.")
