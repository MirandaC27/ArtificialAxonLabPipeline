import HelperFunctions 
import sys

if __name__ == "__main__":
    func_name = sys.argv[1]

    if func_name == "CleanedFileName":
        result = HelperFunctions.CleanedFileName(sys.argv[2])
        print(result)