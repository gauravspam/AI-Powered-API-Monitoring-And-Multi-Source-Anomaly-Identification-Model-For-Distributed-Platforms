import { TextField, MenuItem } from '@mui/material';

const environments = ['All', 'On Prem', 'AWS', 'GCP', 'Azure', 'Multi Cloud'];

export const EnvironmentFilter = ({ value, onChange, allOptionLabel = 'All Environments' }) => {
  return (
    <TextField
      select
      label="Environment"
      value={value}
      onChange={onChange}
      size="small"
      sx={{ minWidth: 200 }}
    >
      {environments.map((env) => (
        <MenuItem key={env} value={env}>
          {env === 'All' ? allOptionLabel : env}
        </MenuItem>
      ))}
    </TextField>
  );
};

export default EnvironmentFilter;
