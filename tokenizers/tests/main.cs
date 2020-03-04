using OpenQA.Selenium;

namespace CalculatorUITestFramework {
    /// <summary>
    /// </summary>
    public static class CalculatorApp {
        public static WindowsElement Window => session.FindElementByClassName();

        /// <summary>
        /// <returns>The sum of two numbers wow.</returns>
        public int AddNumbers(int number1, int number2) {
            int result = number1 + number2;
            return result;
        }

        /// <summary>
        /// <returns>The sum of two numbers wow.</returns>
        public static void int main(String[] args) {
            return 0;
        }
    }
}
