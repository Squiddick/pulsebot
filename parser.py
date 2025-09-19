from PIL import Image
from io import BytesIO
from Logger import Logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select



class ParseWebPage:
    def __init__(self):
        self.logger = Logger()

    def driver_gen(self):
        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=560,810")  # просто подобрать размер окна
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        yield driver
        driver.quit()

    def takeScreenshot(self):
        gen = self.driver_gen()
        driver = next(gen)
        try:
            driver.get("https://www.bryanbraun.com/your-life/weeks.html")
            driver.execute_script("document.body.style.zoom='0.8'")  # 80%
            try:
                month = Select(driver.find_element(By.CLASS_NAME, "month"))
                day = driver.find_element(By.CLASS_NAME, "day")
                year = driver.find_element(By.CLASS_NAME, "year")
                month.select_by_value("11")
                day.send_keys("15")
                year.send_keys("2005")
            except Exception as ex:
                self.logger.warning(ex, exc_info=True)
            png = driver.get_screenshot_as_png()
            im = Image.open(BytesIO(png))
            return png
        finally:
            try:
                next(gen)
            except StopIteration:
                pass

    def saveProcessed(self):
        png = self.takeScreenshot()
        im = Image.open(BytesIO(png))
        width, height = im.size
        left = 7
        upper = 80
        cropped = im.crop((left, upper + 20, width - 12, height - 20))
        image_saved_to_buffer = BytesIO()
        cropped.save(image_saved_to_buffer, format="PNG")
        image_saved_to_buffer.seek(0)
        return image_saved_to_buffer
        self.logger.warning("File was successufuly saved!")