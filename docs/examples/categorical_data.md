# Categorical Data Examples

This section demonstrates how to visualize `categorical` data sources using EViz's autoviz command-line interface.
These sources are identified by using the `-s categorical` option.

## Penguins Dataset

This example demonstrates basic scatter and box plots using the Palmer Penguins dataset, showing relationships between physical measurements and species.

### Scatter and Box Plots

```bash
python autoviz.py -s categorical -f config/examples/categorical/penguins.yaml
```

**What this does:**

- Creates a **scatter plot** showing the relationship between bill length and bill depth, colored by species
- Creates a **box plot** showing the distribution of bill length across different penguin species
- Uses transparency and custom styling for better visualization

**Configuration highlights:**

- Scatter plot with color grouping by categorical variable (species)
- Box plot with grouping to compare distributions across categories
- Custom alpha transparency and marker size for scatter plots
- Mean values displayed on box plots

**Expected output:**

![Penguins Scatter Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.2/penguins_scatter_bill_dimensions.png)

*Scatter plot showing bill length vs. bill depth colored by penguin species*

![Penguins Box Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.2/penguins_box_bill_length_by_species.png)

*Box plot comparing bill length distribution across penguin species*

---

## Cars Dataset

This example demonstrates a comprehensive set of categorical visualizations using automotive data, showcasing multiple plot types for different analytical purposes.

### Multiple Plot Types

```bash
python autoviz.py -s categorical -f config/examples/categorical/cars.yaml
```

**What this does:**

- Creates **5 different plot types** to analyze various aspects of the cars dataset:
  - **Histogram**: Distribution of miles per gallon (mpg)
  - **Bar chart**: Average horsepower by region of origin
  - **Pie chart**: Proportion of vehicles by number of cylinders
  - **Scatter plot**: Relationship between weight and fuel efficiency (mpg)
  - **Box plot**: MPG distribution across different cylinder counts

**Configuration highlights:**

- Histogram with mean indicator for understanding central tendency
- Bar chart with value labels and custom orientation
- Pie chart with percentage labels and custom start angle
- Scatter plot with custom markers
- Box plot grouped by categorical variable with mean values

**Expected output:**

![Cars Histogram](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.2/cars_hist_mpg.png)

*Histogram showing the distribution of miles per gallon (mpg)*

![Cars Bar Chart](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.2/cars_bar_horsepower_by_origin.png)

*Bar chart comparing average horsepower by region of origin*

![Cars Pie Chart](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.2/cars_pie_cylinders.png)

*Pie chart showing proportion of vehicles by number of cylinders*

![Cars Scatter Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.2/cars_scatter_weight_vs_mpg.png)

*Scatter plot showing relationship between vehicle weight and fuel efficiency*

![Cars Box Plot](https://github.com/cacruz/eviz-dev/releases/download/docs-images-v0.9.2/cars_box_mpg_by_cylinders.png)

*Box plot comparing mpg distribution across different cylinder counts*

---

## Plot Types Available

EViz supports the following categorical plot types:

- **histogram (hist)**: Show distribution of continuous variables
- **bar chart (bar)**: Compare values across categories with aggregation
- **pie chart (pie)**: Show proportions of a whole
- **scatter plot (scatter)**: Explore relationships between two continuous variables, optionally colored by category
- **box plot (box)**: Display distribution statistics and compare across categories

## Configuration Tips

- **YAML files** control plot types, variables to plot, and output options
- **Specs files** customize plot appearance (colors, titles, styling, etc.)
- **Grouping**: Use `by` parameter for box plots and `color` for scatter plots to group by categorical variables
- **Customization**: Modify specs files to adjust colors, transparency, marker styles, and more
- **Check config templates** in `config/examples/categorical/` for examples
- **Use absolute paths** or environment variables (like `${HOME}`) in configuration files for reliable data access
