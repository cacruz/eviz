import pytest
import numpy as np
import xarray as xr
from unittest.mock import MagicMock
from eviz.lib.data.sources.base import DataSource


class ConcreteDataSource(DataSource):
    """Concrete implementation of DataSource for testing."""
    def load_data(self, file_path):
        """Load data from the specified file path."""
        self.dataset = xr.Dataset(
            data_vars={
                'temperature': xr.DataArray(
                    data=np.random.rand(2, 3, 4),
                    dims=['time', 'lat', 'lon'],
                    coords={
                        'time': np.array(['2022-01-01', '2022-01-02'], dtype='datetime64[D]'),
                        'lat': np.array([0, 45, 90]),
                        'lon': np.array([0, 90, 180, 270])
                    }
                )
            }
        )
        return self.dataset


class TestDataSource:
    """Test cases for the DataSource class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.data_source = ConcreteDataSource('test_model')
        
        self.test_dataset = xr.Dataset(
            data_vars={
                'temperature': xr.DataArray(
                    data=np.random.rand(2, 3, 4),
                    dims=['time', 'lat', 'lon'],
                    coords={
                        'time': np.array(['2022-01-01', '2022-01-02'], dtype='datetime64[D]'),
                        'lat': np.array([0, 45, 90]),
                        'lon': np.array([0, 90, 180, 270])
                    }
                ),
                'pressure': xr.DataArray(
                    data=np.random.rand(2, 3, 4),
                    dims=['time', 'lat', 'lon'],
                    coords={
                        'time': np.array(['2022-01-01', '2022-01-02'], dtype='datetime64[D]'),
                        'lat': np.array([0, 45, 90]),
                        'lon': np.array([0, 90, 180, 270])
                    }
                )
            }
        )
        
        self.data_source.dataset = self.test_dataset
    
    def test_init(self):
        """Test initialization of DataSource."""
        assert self.data_source.model_name == 'test_model'
        assert self.data_source.dataset is not None
        assert self.data_source.metadata == {}
    
    def test_load_data(self):
        """Test loading data."""
        data_source = ConcreteDataSource('test_model')
        
        result = data_source.load_data('test_file.nc')
        assert result is not None
        assert isinstance(result, xr.Dataset)
        assert 'temperature' in result.data_vars
    
    def test_validate_data(self):
        """Test validating data."""
        result = self.data_source.validate_data()
        assert result is True
    
    def test_validate_data_no_dataset(self):
        """Test validating data with no dataset."""
        data_source = ConcreteDataSource('test_model')
        
        result = data_source.validate_data()
        assert result is False
    
    def test_get_field(self):
        """Test getting a field."""
        result = self.data_source.get_field('temperature')
        assert result is not None
        assert isinstance(result, xr.DataArray)
        assert result.dims == ('time', 'lat', 'lon')
    
    def test_get_field_not_found(self):
        """Test getting a field that doesn't exist."""
        result = self.data_source.get_field('non_existent')
        assert result is None
    
    def test_get_field_no_dataset(self):
        """Test getting a field with no dataset."""
        data_source = ConcreteDataSource('test_model')
        result = data_source.get_field('temperature')
        assert result is None
    
    def test_get_metadata(self):
        """Test getting metadata."""
        self.data_source.metadata = {'key': 'value'}
        result = self.data_source.get_metadata()
        assert result == {'key': 'value'}
    
    def test_get_dimensions(self):
        """Test getting dimensions."""
        result = self.data_source.get_dimensions()
        assert result == ['time', 'lat', 'lon']
    
    def test_get_dimensions_no_dataset(self):
        """Test getting dimensions with no dataset."""
        data_source = ConcreteDataSource('test_model')
        result = data_source.get_dimensions()
        assert result == []
    
    def test_get_variables(self):
        """Test getting variables."""
        result = self.data_source.get_variables()
        assert result == ['temperature', 'pressure']
    
    def test_get_variables_no_dataset(self):
        """Test getting variables with no dataset."""
        data_source = ConcreteDataSource('test_model')
        result = data_source.get_variables()
        assert result == []
    
    def test_close(self):
        """Test closing the data source."""
        self.data_source.dataset = MagicMock()
        self.data_source.dataset.close = MagicMock()        
        self.data_source.close()
        self.data_source.dataset.close.assert_called_once()
    
    def test_getattr(self):
        """Test getting an attribute from the dataset."""
        self.data_source.dataset = MagicMock()
        self.data_source.dataset.dims = ('time', 'lat', 'lon')
        
        result = self.data_source.dims
        assert result == ('time', 'lat', 'lon')

    def test_getitem(self):
        """Test getting an item from the dataset."""
        result = self.data_source['temperature']
        
        assert result is not None
        assert isinstance(result, xr.DataArray)
        assert result.dims == ('time', 'lat', 'lon')
    
    def test_getitem_no_dataset(self):
        """Test getting an item with no dataset."""
        data_source = ConcreteDataSource('test_model')
        with pytest.raises(TypeError):
            data_source['temperature']


# ---------------------------------------------------------------------------
# Shared meta_coords fixture used by the two new test classes below
# ---------------------------------------------------------------------------
_EXTRA_META_COORDS = {
    'xc': {'gridded': 'lon,longitude'},
    'yc': {'gridded': 'lat,latitude'},
    'zc': {'gridded': 'lev,level'},
    'tc': {'gridded': 'time'},
    'extra': {
        'bc': {
            'gridded': 'bnds,band,bands',
            'fldas':   'bnds',
        },
        'bounds': {
            'gridded': 'bnds,bounds,nv,nbnd',
        },
    },
}


def _make_source_with_meta(model_name='gridded'):
    source = ConcreteDataSource(model_name)
    mock_cm = MagicMock()
    mock_cm.meta_coords = _EXTRA_META_COORDS
    source.config_manager = mock_cm
    return source


class TestGetModelDimNameExtra:
    """Tests for extra.* dotted-path support in DataSource._get_model_dim_name."""

    def test_bc_returns_bnds_when_present(self):
        source = _make_source_with_meta()
        assert source._get_model_dim_name('extra.bc', ['time', 'lon', 'lat', 'bnds']) == 'bnds'

    def test_bc_returns_none_when_absent(self):
        source = _make_source_with_meta()
        assert source._get_model_dim_name('extra.bc', ['time', 'lon', 'lat']) is None

    def test_bc_matches_band_alias(self):
        source = _make_source_with_meta()
        assert source._get_model_dim_name('extra.bc', ['time', 'lon', 'lat', 'band']) == 'band'

    def test_bc_matches_bands_alias(self):
        source = _make_source_with_meta()
        assert source._get_model_dim_name('extra.bc', ['time', 'lon', 'lat', 'bands']) == 'bands'

    def test_bounds_matches_bounds_dim(self):
        source = _make_source_with_meta()
        assert source._get_model_dim_name('extra.bounds', ['time', 'lon', 'lat', 'bounds']) == 'bounds'

    def test_bounds_matches_nv_alias(self):
        source = _make_source_with_meta()
        assert source._get_model_dim_name('extra.bounds', ['time', 'lon', 'lat', 'nv']) == 'nv'

    def test_unknown_slot_returns_none(self):
        source = _make_source_with_meta()
        assert source._get_model_dim_name('extra.nosuchslot', ['time', 'lon', 'lat', 'bnds']) is None

    def test_unknown_section_returns_none(self):
        source = _make_source_with_meta()
        assert source._get_model_dim_name('nosection.bc', ['bnds']) is None

    def test_model_specific_entry_used_when_present(self):
        source = _make_source_with_meta(model_name='fldas')
        assert source._get_model_dim_name('extra.bc', ['time', 'lon', 'lat', 'bnds']) == 'bnds'

    def test_falls_back_to_gridded_for_unknown_model(self):
        source = _make_source_with_meta(model_name='unknown_model')
        assert source._get_model_dim_name('extra.bc', ['time', 'lon', 'lat', 'bnds']) == 'bnds'

    def test_standard_dims_unaffected_by_extra_section(self):
        source = _make_source_with_meta()
        assert source._get_model_dim_name('xc', ['lon', 'lat', 'time', 'bnds']) == 'lon'

    def test_no_config_manager_returns_none(self):
        source = ConcreteDataSource('gridded')
        assert source._get_model_dim_name('extra.bc', ['bnds']) is None


class TestGetExtraDimNames:
    """Tests for DataSource._get_extra_dim_names."""

    def test_returns_matched_dims(self):
        source = _make_source_with_meta()
        result = source._get_extra_dim_names(['time', 'lon', 'lat', 'bnds'])
        assert result['bc'] == 'bnds'
        assert result['bounds'] == 'bnds'

    def test_returns_none_for_unmatched_slots(self):
        source = _make_source_with_meta()
        result = source._get_extra_dim_names(['time', 'lon', 'lat'])
        assert all(v is None for v in result.values())

    def test_keys_match_extra_section_slots(self):
        source = _make_source_with_meta()
        result = source._get_extra_dim_names([])
        assert set(result.keys()) == {'bc', 'bounds'}

    def test_returns_empty_dict_without_config_manager(self):
        source = ConcreteDataSource('gridded')
        assert source._get_extra_dim_names(['bnds']) == {}

    def test_band_alias_matched_for_bc(self):
        source = _make_source_with_meta()
        result = source._get_extra_dim_names(['time', 'lon', 'lat', 'band'])
        assert result['bc'] == 'band'
        assert result['bounds'] is None


class TestResolveCoordValue:
    """Tests for DataSource._resolve_coord_value."""

    def setup_method(self):
        self.source = _make_source_with_meta()

    def test_string_match(self):
        assert self.source._resolve_coord_value('lon', ['lat', 'lon'], 'xc') == 'lon'

    def test_string_no_match_returns_value(self):
        # Single-token strings are returned as-is regardless of available_dims;
        # filtering only applies to comma-separated lists.
        assert self.source._resolve_coord_value('lon', ['lat', 'time'], 'xc') == 'lon'

    def test_string_csv_first_match(self):
        assert self.source._resolve_coord_value('lon,longitude,x', ['longitude', 'lat'], 'xc') == 'longitude'

    def test_string_csv_no_match(self):
        assert self.source._resolve_coord_value('lon,longitude,x', ['lat', 'time'], 'xc') is None

    def test_string_csv_no_available_dims_returns_first(self):
        assert self.source._resolve_coord_value('lon,longitude,x', None, 'xc') == 'lon'

    def test_list_match(self):
        assert self.source._resolve_coord_value(['lon', 'longitude'], ['latitude', 'longitude'], 'xc') == 'longitude'

    def test_list_no_match_returns_first(self):
        assert self.source._resolve_coord_value(['lon', 'longitude'], ['lat', 'time'], 'xc') == 'lon'

    def test_dict_dim_key_match(self):
        assert self.source._resolve_coord_value({'dim': 'west_east'}, ['west_east', 'south_north'], 'xc') == 'west_east'

    def test_dict_dim_key_csv(self):
        assert self.source._resolve_coord_value(
            {'dim': 'bottom_top,bottom_top_stag'}, ['bottom_top_stag'], 'zc'
        ) == 'bottom_top_stag'

    def test_dict_dim_key_no_match(self):
        assert self.source._resolve_coord_value({'dim': 'west_east'}, ['lat', 'lon'], 'xc') is None

    def test_dict_coords_key(self):
        assert self.source._resolve_coord_value({'coords': 'XLONG'}, ['XLONG', 'lat'], 'xc') == 'XLONG'
