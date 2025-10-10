"""Unified box plot plotter for both gridded and categorical data using Matplotlib."""

import matplotlib as mpl
import numpy as np
import pandas as pd
import logging
import matplotlib.pyplot as plt
import eviz.lib.autoviz.utils as pu

from .base import MatplotlibBasePlotter


class MatplotlibBoxPlotter(MatplotlibBasePlotter):
    """Matplotlib implementation of box plotting for both gridded and categorical data."""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)

    def plot(self, config, data_to_plot):
        """Create a box plot using Matplotlib.

        Handles two types of data:
        1. Gridded data: (data, categories, values, field_name, plot_type, findex, fig, [original_data_array])
        2. Categorical data: (data, field_name, plot_type, findex, fig, plot_options, plot_params)

        Args:
            config: Configuration manager
            data_to_plot: Tuple with data and plotting parameters

        Returns:
            The created/updated figure
        """
        # Detect data type based on tuple structure
        if self._is_categorical_data(data_to_plot):
            return self._plot_categorical(config, data_to_plot)
        else:
            return self._plot_gridded(config, data_to_plot)

    def _is_categorical_data(self, data_to_plot):
        """Detect if this is categorical data based on tuple structure.

        Categorical data has:
        - DataFrame as first element
        - field_name as second element (string)
        - 6 or 7 elements total

        Gridded data has:
        - DataFrame with 'value' and 'experiment' columns
        - Second element is None (categories placeholder)
        - 7 or 8 elements total
        """
        if len(data_to_plot) < 6:
            return False

        # Check the second element - if it's None, it's gridded data
        # Gridded: (data, None, None, field_name, ...)
        # Categorical: (data, field_name, plot_type, ...)
        second_elem = data_to_plot[1]
        if second_elem is None:
            return False  # Gridded

        # Check if second element is a string (field_name for categorical)
        if isinstance(second_elem, str):
            # Additional check: gridded has (data, categories, values, field_name, ...)
            # where categories and values could be something, but element 2 (index 1,2) would not both be strings
            # Categorical has (data, field_name, plot_type, ...)
            # If element 2 (index 2) is a string like 'box', it's categorical
            if len(data_to_plot) > 2 and isinstance(data_to_plot[2], str):
                # Check if it's a plot type
                if data_to_plot[2] in ['box', 'boxplot', 'scatter', 'line', 'bar', 'pie', 'hist']:
                    return True

        # Check if first element is a DataFrame with gridded structure
        first_elem = data_to_plot[0]
        if isinstance(first_elem, pd.DataFrame):
            # Gridded box plots have 'value' and 'experiment' columns
            if 'value' in first_elem.columns and 'experiment' in first_elem.columns:
                return False  # Gridded
            else:
                return True  # Categorical

        return False

    def _plot_gridded(self, config, data_to_plot):
        """Create box plot for gridded data.

        Args:
            config: Configuration manager
            data_to_plot: Tuple containing (data, categories, values, field_name, plot_type, findex, fig, [original_data_array])

        Returns:
            The created figure
        """
        # Handle both 7-element and 8-element tuples for backward compatibility
        if len(data_to_plot) == 8:
            data, _, _, field_name, plot_type, findex, fig, original_data_array = data_to_plot
        else:
            data, _, _, field_name, plot_type, findex, fig = data_to_plot
            original_data_array = None

        if data is None or not isinstance(data, pd.DataFrame) or data.empty:
            return fig

        required_cols = {'value', 'experiment'}
        if not required_cols.issubset(data.columns):
            self.logger.warning(f"DataFrame missing required columns: "
                                f"{required_cols - set(data.columns)}")
            return fig

        self.source_name = config.source_names[config.ds_index]
        # Use original DataArray for units extraction if available, otherwise fall back to DataFrame
        units_data = original_data_array if original_data_array is not None else data
        self.units = self.get_units(config,
                                    field_name,
                                    units_data,
                                    findex)
        self.fig = fig
        self.ax_opts = config.ax_opts
        df = data

        if not config.compare and not config.compare_diff and not config.overlay:
            fig.set_axes()

        ax_temp = fig.get_axes()
        axes_shape = fig.subplots

        if axes_shape == (3, 1):
            if self.ax_opts['is_diff_field']:
                self.ax = ax_temp[2]
            else:
                self.ax = ax_temp[config.axindex]
        elif axes_shape == (2, 2):
            if self.ax_opts['is_diff_field']:
                self.ax = ax_temp[2]
                if self.ax_opts['add_extra_field_type']:
                    self.ax = ax_temp[3]
            else:
                self.ax = ax_temp[config.axindex]
        elif axes_shape == (1, 2) or axes_shape == (1, 3):
            if isinstance(ax_temp, list):
                self.ax = ax_temp[config.axindex]
            else:
                self.ax = ax_temp
        else:
            self.ax = ax_temp[0]

        self.ax_opts = fig.update_ax_opts(field_name, self.ax, 'box', level=0)
        # Use original DataArray for plot_text if available, otherwise use DataFrame
        text_data = original_data_array if original_data_array is not None else df
        self.plot_text(config, field_name, 'box', data=text_data)

        self._plot_gridded_box_data(config, fig, df, field_name, findex, original_data_array)

        # Handle title for comparison plots
        if config.compare_diff:
            title_str = field_name
            if 'name' in config.spec_data[field_name]:
                title_str = config.spec_data[field_name]['name']
            fig.suptitle_eviz(title_str, ha='left',
                            fontweight='bold', fontstyle='italic',
                            fontsize=self._image_font_size(fig.subplots))
        elif config.compare:
            title_str = config.map_params[findex].get('field', 'No name')
            if hasattr(config, 'spec_data') and field_name in config.spec_data and \
                    'name' in config.spec_data[field_name]:
                title_text = config.spec_data[field_name]['name']
            fig.suptitle_eviz(title_text,  ha='left',
                            fontweight='bold', fontstyle='italic',
                            fontsize=self._image_font_size(fig.subplots))

            if config.add_logo:
                pu.add_logo_ax(fig, desired_width_ratio=0.05)

        return fig

    def _plot_gridded_box_data(self, config, fig, df, field_name, findex, original_data_array=None):
        """Helper method that plots the box plot data for gridded data."""
        ax = self.ax
        ax_opts = self.ax_opts
        with mpl.rc_context(rc=ax_opts.get('rc_params', {})):
            title = field_name
            if hasattr(config, 'spec_data') and \
                    field_name in config.spec_data and \
                    'name' in config.spec_data[field_name]:
                title = config.spec_data[field_name]['name']

            # Use original DataArray for units extraction if available
            units_data = original_data_array if original_data_array is not None else df
            units = self.get_units(config, field_name, units_data, findex)

            color_settings = None
            if config.compare or config.compare_diff or config.overlay:
                color_settings = config.box_colors
            else:
                if field_name in config.spec_data and \
                        'boxplot' in config.spec_data[field_name] and \
                        'box_color' in config.spec_data[field_name]['boxplot']:
                    color_settings = config.spec_data[field_name]['boxplot'].get('box_color', 'blue')

            try:
                category_col = None
                if 'time' in df.columns:
                    category_col = 'time'
                elif 'category' in df.columns:
                    category_col = 'category'
                else:
                    # Use the first column that's not 'value'
                    for col in df.columns:
                        if col != 'value':
                            category_col = col
                            break

                if not color_settings:
                    color_settings = ax_opts.get('color_cycle', plt.rcParams['axes.prop_cycle'].by_key()['color'])
                elif isinstance(color_settings, str):
                    color_settings = [color_settings]
                self.logger.debug(f"Using color settings: {color_settings}")

                has_multiple_experiments = 'experiment' in df.columns and len(df['experiment'].unique()) > 1

                if has_multiple_experiments and hasattr(config, 'overlay') and config.overlay:
                    experiments = df['experiment'].unique()
                    num_experiments = len(experiments)

                    all_categories = df[category_col].unique()
                    num_categories = len(all_categories)
                    self.logger.debug(f"Found {num_experiments} experiments and {num_categories} categories")

                    if category_col == 'time':
                        # Try to convert time strings to datetime for proper sorting
                        try:
                            # Convert time strings to datetime objects
                            time_categories = pd.to_datetime(all_categories)
                            # Sort and get the sorted indices
                            sorted_indices = np.argsort(time_categories)
                            # Reorder categories
                            all_categories = [all_categories[i] for i in sorted_indices]
                        except:
                            # If conversion fails, try numeric sorting
                            try:
                                # Try to convert to numeric values
                                numeric_categories = [float(cat) for cat in all_categories]
                                sorted_indices = np.argsort(numeric_categories)
                                all_categories = [all_categories[i] for i in sorted_indices]
                            except:
                                # If all else fails, use lexicographic sorting
                                all_categories = sorted(all_categories)

                    positions = []
                    box_data = []
                    box_colors = []

                    group_width = 0.8
                    box_width = group_width / num_experiments

                    for i, category in enumerate(all_categories):
                        category_center = i + 1  # Center position for this category group

                        for j, experiment in enumerate(experiments):
                            # Calculate offset from center for this experiment's box
                            offset = (j - (num_experiments - 1) / 2) * box_width
                            position = category_center + offset

                            mask = (df[category_col] == category) & (df['experiment'] == experiment)
                            values = df.loc[mask, 'value'].values

                            if len(values) > 0:
                                positions.append(position)
                                box_data.append(values)

                                if len(color_settings) == 1:
                                    box_colors.append(color_settings[0])
                                else:
                                    box_colors.append(color_settings[j % len(color_settings)])

                    exp_ids = df['experiment'].unique().tolist()
                    box_data = [df[df['experiment'] == eid]['value'] for eid in exp_ids]

                    box_plot = ax.boxplot(box_data,
                                positions=positions,
                                patch_artist=True,
                                labels=None,  # Don't set labels here
                                widths=box_width * 0.9)

                    for i, box in enumerate(box_plot['boxes']):
                        box.set(facecolor=box_colors[i % len(box_colors)], alpha=0.7)

                    # Calculate and display RMSE if we have multiple experiments
                    if num_experiments > 1:
                        # Use the first experiment as reference
                        reference_exp = experiments[0]
                        reference_data = df[df['experiment'] == reference_exp]['value']

                        # Calculate RMSE for each experiment compared to reference
                        for i, experiment in enumerate(experiments[1:], 1):  # Skip reference experiment
                            comparison_data = df[df['experiment'] == experiment]['value']
                            rmse = self._calculate_rmse(reference_data, comparison_data)

                            # TODO: Move this to figure.py? Make optional?
                            if not np.isnan(rmse):
                                # Format RMSE value with appropriate precision
                                rmse_text = f"RMSE({reference_exp}, {experiment}) = {rmse:.3f} {units}"

                                # Position the text in upper right corner
                                # Stagger vertically for multiple comparisons
                                # y_pos = 1.02 + (i-1) * 0.04
                                # ax.text(0.85, y_pos, rmse_text,
                                # centered above the box plots
                                # Stagger vertically for multiple comparisons
                                y_pos = 1.05 - (i-1) * 0.05
                                ax.text(0.5, y_pos, rmse_text,
                                    transform=ax.transAxes,
                                    horizontalalignment='center',
                                    verticalalignment='top',
                                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=3),
                                    fontsize=8)

                    if not config.add_legend:
                        if len(all_categories) == 1:
                            # Only one category: label by experiment
                            ax.set_xticks(positions)
                            ax.set_xticklabels(experiments)
                        else:
                            # Multiple categories: label by category
                            category_centers = [i + 1 for i in range(num_categories)]
                            ax.set_xticks(category_centers)
                            ax.set_xticklabels(all_categories, rotation=45, ha='right', fontsize=8)
                    else:
                        legend_handles = [plt.Rectangle((0, 0), 1, 1, color=box_colors[i % len(box_colors)], alpha=0.7)
                                        for i in range(num_experiments)]
                        ax.legend(legend_handles, experiments, loc='best')

                    if config.add_legend:
                        ax.set_xlabel(category_col)
                    ax.set_xlim(0.5, num_categories + 0.5)
                    ax.set_ylabel(f"{title} ({units})")
                    ax.grid(ax_opts['add_grid'], linestyle='--', alpha=0.7)

                else:
                    # Standard box plot (single experiment or not overlaid)
                    # Group data by category
                    grouped_data = df.groupby(category_col)['value'].apply(list).to_dict()
                    categories = list(grouped_data.keys())
                    values = [grouped_data[cat] for cat in categories]

                    if category_col == 'time':
                        try:
                            # Convert time strings to datetime objects
                            time_categories = pd.to_datetime(categories)
                            # Sort and get the sorted indices
                            sorted_indices = np.argsort(time_categories)
                            # Reorder categories
                            sorted_categories = [categories[i] for i in sorted_indices]
                            # Reorder values to match sorted categories
                            values = [grouped_data[categories[i]] for i in sorted_indices]
                            categories = sorted_categories
                        except:
                            # If conversion fails, try numeric sorting
                            try:
                                # Try to convert to numeric values
                                numeric_categories = [float(cat) for cat in categories]
                                sorted_indices = np.argsort(numeric_categories)
                                sorted_categories = [categories[i] for i in sorted_indices]
                                values = [grouped_data[categories[i]] for i in sorted_indices]
                                categories = sorted_categories
                            except:
                                # If all else fails, use lexicographic sorting
                                sorted_categories = sorted(categories)
                                values = [grouped_data[cat] for cat in sorted_categories]
                                categories = sorted_categories
                    else:
                        values = [grouped_data[cat] for cat in categories]

                    # Format labels
                    formatted_labels = []
                    for cat in categories:
                        try:
                            dt = pd.to_datetime(cat)
                            formatted_labels.append(dt.strftime('%H:%M'))  # Just show hour:minute
                        except:
                            formatted_labels.append(cat)

                    exp_id = df['experiment'].iloc[0] if 'experiment' in df.columns else ''

                    # If only one experiment, use exp_id as label
                    if 'experiment' in df.columns and df['experiment'].nunique() == 1:
                        exp_id = df['experiment'].iloc[0]
                        box_plot = ax.boxplot(values,
                                    patch_artist=True,
                                    labels=[exp_id]*len(values))
                        ax.set_xticklabels([exp_id]*len(values), fontsize=10)
                    else:
                        box_plot = ax.boxplot(values,
                                    patch_artist=True,
                                    labels=categories)
                        ax.set_xticklabels(formatted_labels, rotation=45, ha='right', fontsize=10)

                    # TODO: Move this to figure.py? Make optional?
                    rmse = self._calculate_rmse_from_mean(values)
                    if not np.isnan(rmse):
                        rmse_text = f"RMSE from mean = {rmse:.3f} {units}"
                        # Position the text in upper right corner
                        ax.text(0.85, 1.02, rmse_text,
                            transform=ax.transAxes,
                            horizontalalignment='center',
                            verticalalignment='bottom',
                            bbox=dict(facecolor='white', alpha=0.7, edgecolor='none', pad=3),
                            fontsize=8)

                    ax.set_xlabel(category_col)
                    ax.set_ylabel(f"{title} ({units})")
                    ax.grid(ax_opts['add_grid'], linestyle='--', alpha=0.7)

                if config.compare:
                    fig.suptitle_eviz(text=field_name,
                                    fontweight='bold',
                                    fontstyle='italic',
                                    fontsize=self._image_font_size(fig.subplots))

                if config.add_logo:
                    self._add_logo_ax(fig, desired_width_ratio=0.05)

            except Exception as e:
                self.logger.error(f"Error creating matplotlib box plot: {e}")
                import traceback
                self.logger.error(traceback.format_exc())

    def _plot_categorical(self, config, data_to_plot):
        """Create box plot for categorical/CSV data.

        Args:
            config: Configuration manager
            data_to_plot: Tuple containing (data, field_name, plot_type, findex, fig, plot_options, plot_params)

        Returns:
            The created/updated figure
        """
        # Unpack data_to_plot with backward compatibility
        plot_params = {}
        if len(data_to_plot) >= 7:
            data, field_name, plot_type, findex, fig, plot_options, plot_params = data_to_plot[:7]
        elif len(data_to_plot) == 6:
            data, field_name, plot_type, findex, fig, plot_options = data_to_plot
        else:
            # Fallback for older format
            data, field_name, plot_type, findex, fig = data_to_plot[:5]
            plot_options = data_to_plot[5] if len(data_to_plot) > 5 else {}

        if data is None or (isinstance(data, pd.DataFrame) and data.empty):
            self.logger.warning(f"No data available for {field_name}")
            return fig

        self.fig = fig
        self.ax_opts = config.ax_opts if hasattr(config, 'ax_opts') else {}

        # Set up axes
        if not config.compare and not config.compare_diff:
            if fig.get_axes() is None or len(fig.get_axes()) == 0:
                fig.set_axes()

        ax_temp = fig.get_axes()
        if isinstance(ax_temp, list) and len(ax_temp) > 0:
            self.ax = ax_temp[0]
        else:
            self.ax = ax_temp

        self._plot_categorical_box_data(config, data, field_name, plot_options, plot_params)

        return fig

    def _plot_categorical_box_data(self, config, data, field_name, plot_options, plot_params):
        """Create the actual box plot for categorical data.

        Args:
            config: Configuration manager
            data: pandas DataFrame
            field_name: Name of the field being plotted
            plot_options: Dictionary of plotting options
            plot_params: Dictionary of plot parameters (y, by for categorical data)
        """
        ax = self.ax

        with mpl.rc_context(rc=self.ax_opts.get('rc_params', {})):
            # Handle categorical data with plot_params (y, by)
            if plot_params and 'y' in plot_params:
                y_col = plot_params['y']
                by_col = plot_params.get('by', None)

                if not isinstance(data, pd.DataFrame):
                    self.logger.error("Box plot requires DataFrame")
                    return

                if y_col not in data.columns:
                    self.logger.error(f"Column {y_col} not found in DataFrame")
                    return

                if by_col:
                    # Grouped box plot
                    if by_col not in data.columns:
                        self.logger.error(f"Column {by_col} not found in DataFrame")
                        return

                    # Prepare data
                    categories = data[by_col].unique()
                    box_data = [data[data[by_col] == cat][y_col].dropna().values for cat in categories]

                    bp = ax.boxplot(
                        box_data,
                        labels=[str(cat) for cat in categories],
                        patch_artist=True,
                        showmeans=plot_options.get('showmeans', False),
                        meanline=plot_options.get('meanline', False),
                        notch=plot_options.get('notch', False),
                        vert=plot_options.get('vert', True)
                    )

                    # Color the boxes
                    box_color = plot_options.get('color', 'lightblue')
                    for patch in bp['boxes']:
                        patch.set_facecolor(box_color)
                        patch.set_alpha(plot_options.get('alpha', 0.7))

                    xlabel = by_col
                    ylabel = y_col
                else:
                    # Single box plot
                    values = data[y_col].dropna().values
                    bp = ax.boxplot(
                        [values],
                        labels=[y_col],
                        patch_artist=True,
                        showmeans=plot_options.get('showmeans', False),
                        meanline=plot_options.get('meanline', False),
                        notch=plot_options.get('notch', False),
                        vert=plot_options.get('vert', True)
                    )

                    # Color the box
                    box_color = plot_options.get('color', 'lightblue')
                    for patch in bp['boxes']:
                        patch.set_facecolor(box_color)
                        patch.set_alpha(plot_options.get('alpha', 0.7))

                    xlabel = 'Variable'
                    ylabel = y_col
            else:
                self.logger.error("Box plot requires 'y' parameter in plot_params")
                return

            ax.set_xlabel(xlabel, fontsize=plot_options.get('xlabel_fontsize', 10))
            ax.set_ylabel(ylabel, fontsize=plot_options.get('ylabel_fontsize', 10))

            if by_col:
                title = plot_options.get('title', f'{ylabel} by {xlabel}')
                ax.set_title(title, fontsize=plot_options.get('title_fontsize', 12))

            if plot_options.get('grid', True):
                ax.grid(axis='y', alpha=0.3, linestyle='--')

            # Rotate x-axis labels if requested
            if plot_options.get('rotate_labels', False):
                plt.setp(ax.get_xticklabels(), rotation=45, ha='right')

            num_boxes = len(box_data) if by_col else 1
            self.logger.info(f"Created box plot for {field_name} with {num_boxes} box(es)")

    @staticmethod
    def format_time_label(label):
        try:
            # Try parsing as datetime
            dt = pd.to_datetime(label)
            # Option 1: '2018-05-23 06'
            return dt.strftime('%Y-%m-%d %H')
            # Option 2: '05-23 06'
            # return dt.strftime('%m-%d %H')
        except Exception:
            return label[:13]  # fallback

    def _calculate_rmse(self, data1, data2):
        """
        Calculate the Root Mean Square Error (RMSE) between two datasets.

        Args:
            data1 (array-like): First dataset
            data2 (array-like): Second dataset

        Returns:
            float: The RMSE value
        """
        # Ensure inputs are numpy arrays
        if isinstance(data1, pd.Series):
            data1 = data1.values
        if isinstance(data2, pd.Series):
            data2 = data2.values

        # Flatten arrays
        if hasattr(data1, 'flatten'):
            data1 = data1.flatten()
        if hasattr(data2, 'flatten'):
            data2 = data2.flatten()

        # Find common indices where both arrays have valid values
        mask = ~(np.isnan(data1) | np.isnan(data2))
        if np.sum(mask) < 2:
            self.logger.error("Not enough valid data points for RMSE calculation")
            return np.nan

        data1_clean = data1[mask]
        data2_clean = data2[mask]

        # Calculate RMSE
        mse = np.mean((data1_clean - data2_clean) ** 2)
        rmse = np.sqrt(mse)

        return rmse

    def _calculate_rmse_from_mean(self, data):
        """
        Calculate RMSE of data from its mean value.

        Args:
            data (array-like): Dataset to evaluate

        Returns:
            float: The RMSE value
        """
        try:
            if isinstance(data, list):
                # Flatten the list of lists into a single list
                flat_data = [item for sublist in data for item in sublist]
                data = np.array(flat_data)

            if isinstance(data, pd.Series):
                data = data.values

            if hasattr(data, 'flatten'):
                data = data.flatten()

            data_clean = data[~np.isnan(data)]

            if len(data_clean) < 2:
                self.logger.error("Not enough valid data points for RMSE calculation")
                return np.nan

            mean_value = np.mean(data_clean)

            # Calculate RMSE from mean
            mse = np.mean((data_clean - mean_value) ** 2)
            rmse = np.sqrt(mse)

            return rmse

        except Exception as e:
            self.logger.error(f"Error calculating RMSE from mean: {e}")
            import traceback
            self.logger.debug(traceback.format_exc())
            return np.nan
