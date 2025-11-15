# Use the official Python image as a base
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- ADD THIS LINE ---
# This copies your local .streamlit folder into the container
COPY ./.streamlit /app/.streamlit
# ---------------------

# Copy the source code into the container
COPY ./src /app/src
COPY ./data /app/data

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the Streamlit app
CMD ["streamlit", "run", "src/app.py"]