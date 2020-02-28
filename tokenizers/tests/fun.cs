using OpenQA.Selenium;

namespace CalculatorUITestFramework {
    /// <summary>
    /// This class contains.
    /// </summary>
    public static class CalculatorApp {
        public static WindowsElement Window => session.FindElementByClassName();

        /// <summary>
        /// Gets sum of two numbers
        /// </summary>
        /// <returns>The sum of two numbers wow.</returns>
        public int AddNumbers(int number1, int number2) {
            int result = number1 + number2;
            return result;
        }
    }
}
