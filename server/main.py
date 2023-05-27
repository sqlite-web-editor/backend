"enter point of application"

import uvicorn


def main():
    "main function"
    uvicorn.run(app="endpoints:App", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
