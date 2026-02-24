# Chapter 1: Streamlit Web Interface (sViz)

Welcome to the first chapter of the EViz tutorial! We're excited to guide you through how EViz helps visualize complex Earth System Model data. We'll start with the most user-friendly part of the system: the Streamlit Web Interface, affectionately known as `sViz`.

## Overview

### What Problem Does sViz Solve?

Imagine you have a lot of scientific data, like temperature readings from different regions or predictions about hurricane paths. Normally, to turn this raw data into beautiful, insightful plots and animations, you'd need to write complex code, learn various plotting libraries, and run scripts from your computer's command line. This can be intimidating and time-consuming, especially for those who aren't expert programmers.

**sViz solves this problem by providing a friendly, easy-to-use website (a "dashboard") where you can simply click, select, and view your visualizations.** It's like having a personal assistant that handles all the complicated coding in the background, showing you the results in your web browser.

#### Our Use Case: Visualizing Earth System Data with a Few Clicks

Let's say you have a dataset from an Earth System Model, and you want to see what's inside. Specifically, you want to:
1.  **Select your dataset.**
2.  **Generate some plots** (like a map of surface pressure or temperature).
3.  **View those plots** and perhaps even filter them.

sViz is designed to make this entire process as smooth as browsing a website!

### Key Concepts: Your Dashboard Explained

Before we dive into using sViz, let's understand a few core ideas:

*   **Web Interface:** Think of it as a website. Instead of typing commands into a black screen, you interact with buttons, dropdowns, and text boxes directly in your web browser (like Chrome, Firefox, or Edge).
*   **Streamlit:** This is the magic tool that makes creating these web interfaces with Python super easy. You write Python code, and Streamlit turns it into an interactive web app without needing you to be a web development expert.
*   **Dashboard:** This is a central place where you can see all your information at a glance. In sViz, it's where you'll find options to pick data, trigger visualizations, and see the resulting images and animations.

## Getting Started

### How to Use sViz

Using sViz is straightforward. You'll run a Python script, and it will open in your web browser.

#### 1. Starting sViz

To get started, you need to open your terminal or command prompt. Navigate to the main (top-level) directory of the EViz project. Then, run the following command:

```bash
streamlit run sviz/sviz.py
```

**What happens?**
This command tells Streamlit to run the `sviz.py` script, which is the heart of our web interface. Streamlit will then automatically open a new tab in your default web browser, displaying the sViz application!

When you first open sViz, you'll see a welcome page with some example visualizations. This page is set up to give you a quick glimpse of what EViz can do.

Here's a simplified look at the code that creates this welcome page in `sviz/sviz.py`:

```python
import streamlit as st
import sys
import os
from pathlib import Path

# ... (path configuration code omitted for simplicity) ...

st.set_page_config(layout="wide") # Makes the page use the full browser width
st.markdown("<h1 style='text-align: center; color: blue;'>sViz</h1>",
            unsafe_allow_html=True) # Displays the main title
st.markdown("<h3 style='text-align: center; color: black;'>A Web-based Approach for Earth System Model Data Visualization</h3>",
            unsafe_allow_html=True) # Displays a subtitle

# Display example images in columns
col1, col2 = st.columns(2)
with col1:
    st.image("https://portal.nccs.nasa.gov/datashare/astg/eviz/sample_data/gif/PSFC.gif",
             use_container_width=True) # Shows an example GIF
with col2:
    st.image("https://portal.nccs.nasa.gov/datashare/astg/eviz/sample_data/gif/RI_SEPA.gif",
             use_container_width=True) # Shows another example GIF

# ... (more images and logo display code omitted) ...
```

**Explanation:**
*   `import streamlit as st`: This line imports the Streamlit library, allowing us to use its functions.
*   `st.set_page_config()`: Configures how the web page looks, like making it wide.
*   `st.markdown()`: Used to display text, including titles and subtitles, formatted with HTML for styling (like `color: blue`).
*   `st.columns(2)`: Creates two columns side-by-side on the page, perfect for arranging images.
*   `st.image()`: Displays an image or GIF from a given URL or file path. `use_container_width=True` makes it fit nicely within its column.

This code works together to create the initial welcoming view of your sViz application.

#### 2. Interacting with the Visualization Page

Once you're on the main sViz page, you'll typically navigate to the "Autoviz" page using the sidebar (if it's configured). This is where the real work happens for creating visualizations.

On the "Autoviz" page (`sviz/pages/autoviz.py`), you'll see interactive elements to achieve our use case:
*   **Select a Dataset:** A dropdown menu will allow you to pick the data you want to visualize.
*   **Enter Dashboard Name:** A text box where you can give your new visualization collection a unique name.

Here's a simplified view of how these interactive elements are created in `sviz/pages/autoviz.py`:

```python
import streamlit as st
# ... (other imports and helper functions omitted) ...

if __name__ == '__main__':
    # ... (code to load dataset options omitted) ...

    st.selectbox(
        "Select a dataset", # Label for the dropdown
        ["None Selected"] + list(single.keys()) + list(compare.keys()), # Options for the dropdown
        key='select_dataset', # Unique identifier for this widget
        on_change=run_metadump # A function to call when selection changes
    )

    dashboard_name = st.text_input(
        'Enter the name of the dashboard you would like to create! (e.g. my_viz)', # Label for the text input
    )

    if dashboard_name:
        # ... (code to trigger visualization generation and page creation) ...
        pass # This is where the magic happens behind the scenes!
```

**Explanation:**
*   `st.selectbox()`: Creates a dropdown menu. You provide a label and a list of options. When you select an option, a function (`run_metadump` in this case) is called to process the selection (more on this in the next section!).
*   `st.text_input()`: Creates a text box where you can type. The text you enter is stored in the `dashboard_name` variable.

When you select a dataset, `sViz` will first gather information about that data using the [Metadump Tool (MetadataExtractor)](03_metadump_tool__metadataextractor__.md). This helps you understand what variables and dimensions are available in your chosen dataset.

Then, once you've entered a dashboard name and triggered the visualization process (by the `if dashboard_name:` condition becoming true and further actions happening), `sViz` works with the [Autoviz Application Core (Autoviz)](02_autoviz_application_core__autoviz__.md) to generate the actual plots and GIFs. Finally, `sViz` will switch you to a new page, uniquely generated for your new dashboard!

#### 3. Viewing Your Generated Plots

After the visualization process is complete, sViz redirects you to a brand-new page (`sviz/pages/{dashboard_name}_{timestamp}.py`). This page is dynamically created just for your visualization session and acts as your personal dashboard for the generated plots.

On this page, you'll see your generated plots and GIFs. You'll also find a sidebar with filtering options (like filtering by model type, field name, or time) to help you explore your visualizations.

The `sviz/other/template.py` file serves as a blueprint for these dynamically generated dashboard pages. It contains the logic to display the plots and implement the filtering.

Here's a simplified look at the `display_vis` function from `sviz/other/template.py` that shows the visualizations:

```python
import streamlit as st
# ... (other imports and helper functions omitted) ...

def display_vis(date_outs, desc_outs):
    """
    Display images from output files.
    """
    if CONFIG['make_gif']: # Check if we should display GIFs
        for date in date_outs.keys():
            with st.expander(date, expanded=True): # Creates an expandable section
                outs = date_outs[date]
                for i, image_url in enumerate(outs):
                    # For GIFs, we embed them using base64 for direct display
                    # ... (GIF embedding code omitted for simplicity) ...
                    pass
    else: # If not GIFs, display static images
        for date in date_outs.keys():
            with st.expander(date, expanded=True):
                # ... (Display description if available) ...
                outs = date_outs[date]
                columns = st.columns(3) # Arrange images in 3 columns
                for i, image_url in enumerate(outs):
                    title = outs[i]['title']
                    time_now = outs[i]['time_now']
                    col_index = i % 3 # Cycle through columns
                    columns[col_index].image(
                        image_url["filename"], use_column_width=True, caption=str(time_now)) # Display image
```

**Explanation:**
*   `st.expander(date, expanded=True)`: Creates a collapsible section on the page. You can click on the header (`date`) to expand or collapse its content.
*   `st.columns(3)`: Organizes the images into three columns, making the layout clean and easy to view.
*   `columns[col_index].image()`: Displays an individual image within one of the columns, along with a `caption` (like the time of the visualization).

This part of `sViz` ensures that once your visualizations are generated, they are presented to you in an organized and interactive way right in your browser.

## Technical Details

### Under the Hood: How sViz Connects Everything

So, how does sViz orchestrate all this? It acts as the "control panel" that talks to other parts of the EViz system.

Here's a simple step-by-step breakdown of what happens when you use sViz to create and view visualizations:

1.  **You start sViz:** You run `streamlit run sviz/sviz.py`.
2.  **Welcome Page:** The main `sviz.py` script loads, showing you the initial welcome page with example GIFs.
3.  **Navigate to Autoviz:** You typically use a sidebar to go to the "Autoviz" application page (`sviz/pages/autoviz.py`).
4.  **Select Data:** On the "Autoviz" page, you pick a dataset from a dropdown.
5.  **Get Data Info:** sViz (specifically, the `autoviz.py` page logic) calls the [Metadump Tool (MetadataExtractor)](03_metadump_tool__metadataextractor__.md) to inspect your chosen dataset and display its details.
6.  **Request Visualization:** You type a name for your dashboard and trigger the visualization process.
7.  **Generate Plots:** sViz calls the core [Autoviz Application Core (Autoviz)](02_autoviz_application_core__autoviz__.md) module, passing it the dataset and configuration. This module then does the heavy lifting of creating plots and GIFs.
8.  **Create Dashboard Page:** Once plots are generated, sViz dynamically creates a new Streamlit page (using `sviz/other/template.py` as a blueprint) specifically for your new set of visualizations.
9.  **Display Results:** You are redirected to this new page, where `template.py`'s logic takes over to display your plots and provide filtering options.

This entire flow can be visualized using a sequence diagram:

```{mermaid}
sequenceDiagram
    participant User
    participant sViz_Main as sViz (Welcome Page)
    participant sViz_Autoviz as sViz (Autoviz Page)
    participant MetadataExtractor as Metadump Tool
    participant Autoviz_Core as Autoviz Core
    participant sViz_Dashboard as sViz (Generated Dashboard)

    User->>sViz_Main: Run `streamlit run sviz/sviz.py`
    sViz_Main-->>User: Display welcome page
    User->>sViz_Autoviz: Navigate to "Autoviz" application
    sViz_Autoviz-->>User: Display dataset selection & dashboard name input
    User->>sViz_Autoviz: Select Dataset
    sViz_Autoviz->>MetadataExtractor: Request dataset info
    MetadataExtractor-->>sViz_Autoviz: Return metadata
    sViz_Autoviz-->>User: Display dataset metadata
    User->>sViz_Autoviz: Enter dashboard name & trigger visualization
    sViz_Autoviz->>Autoviz_Core: Generate plots/GIFs for selected data
    Autoviz_Core-->>sViz_Autoviz: Plots/GIFs generated (saved to disk)
    sViz_Autoviz->>sViz_Dashboard: Dynamically create new Streamlit page (using template)
    sViz_Autoviz-->>User: Redirect to new dashboard page
    sViz_Dashboard-->>User: Display generated plots/GIFs with filters
```

As you can see, sViz acts as the "middleman," providing a user-friendly layer on top of the powerful EViz visualization engine. It makes the complex process of generating and displaying scientific visualizations accessible to everyone.

## Summary

### Conclusion

In this chapter, you've learned that **Streamlit Web Interface (sViz)** is the user-friendly dashboard for the EViz project. It allows you to select datasets, trigger visualization generation, and view results directly in your web browser, abstracting away the underlying complexities. We saw how to start sViz, interact with its elements, and how it uses Streamlit to display information and visualizations.

Most importantly, you now understand that sViz doesn't *create* the visualizations itself; it relies on other powerful components of EViz to do that. The main component sViz interacts with for generating those plots is the `Autoviz Application Core`.

In the next chapter, we'll dive deeper into the core visualization engine: [Autoviz Application Core (Autoviz)](02_autoviz_application_core__autoviz__.md).

---

Generated by [AI Codebase Knowledge Builder](https://github.com/The-Pocket/Tutorial-Codebase-Knowledge)