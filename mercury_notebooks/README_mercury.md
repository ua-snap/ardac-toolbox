# ARDAC notebooks designed for Mercury

Notebooks in the `ardac-toolbox/mercury_notebooks` directory are designed to be run as applications using [Mercury](https://github.com/mljar/mercury). Existing ARDAC notebooks were modified to include an import of `mercury` and an initialization of the app in the first code block. Widgets (eg, text input), if they are used, are also included in the first code block.

### To run a notebook in Mercury:

- Build a virtual environment from `mercury_environment.yml` and activate it. Note that Mercury will not work with Python 3.12!
- In your terminal, navigate to the `ardac-toolbox/mercury_notebooks` directory.
- Execute `mercury run`. The application should open in your browser using port 8000 (http://127.0.0.1:8001/). You may need to manually forward this port on your local machine.
- By default, all notebooks in the `ardac-toolbox/mercury_notebooks` directory will be imported to the notebook gallery.

### Other commands:

- Use `mercury run clear` to clear the application database and start fresh.
- Use `mercury run --verbose` to see more output. This is the only way to see error messages from the application!
