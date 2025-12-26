import { DataGrid } from '@mui/x-data-grid';
import StatusChip from './StatusChip';
import { Box } from '@mui/material';

const columns = [
  { field: 'id', headerName: 'ID', width: 80 },
  { field: 'serviceName', headerName: 'Service', width: 150 },
  { field: 'endpoint', headerName: 'Endpoint', width: 200 },
  { field: 'environment', headerName: 'Environment', width: 130 },
  {
    field: 'severity',
    headerName: 'Severity',
    width: 120,
    renderCell: (params) => <StatusChip value={params.value} type="severity" />,
  },
  {
    field: 'score',
    headerName: 'Score',
    width: 100,
    valueFormatter: (value) => value?.toFixed(2),
  },
  {
    field: 'detectedAt',
    headerName: 'Detected At',
    width: 180,
    valueFormatter: (value) => new Date(value).toLocaleString(),
  },
  {
    field: 'status',
    headerName: 'Status',
    width: 130,
    renderCell: (params) => <StatusChip value={params.value} type="status" />,
  },
];

export const AnomalyTable = ({ rows, onRowClick, loading = false }) => {
  return (
    <Box sx={{ height: 400, width: '100%' }}>
      <DataGrid
        rows={rows}
        columns={columns}
        pageSize={5}
        rowsPerPageOptions={[5, 10, 25]}
        onRowClick={onRowClick}
        loading={loading}
        disableSelectionOnClick
        sx={{
          '& .MuiDataGrid-row:hover': {
            cursor: 'pointer',
          },
        }}
      />
    </Box>
  );
};

export default AnomalyTable;
