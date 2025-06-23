import random
import sys

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <min> <max>")
        sys.exit(1)
    try:
        low = int(sys.argv[1])
        high = int(sys.argv[2])
    except ValueError:
        print("Error: both <min> and <max> must be integers.")
        sys.exit(1)
    if low > high:
        low, high = high, low
    print(random.randint(low, high))

if __name__ == "__main__":
    main()
