import { apisData } from "../data/dummyData";
import { Typography, Table, TableHead, TableRow, TableCell, TableBody } from "@mui/material";

const APIs = () => {
  return (
    <>
      <Typography variant="h4" gutterBottom>APIs</Typography>

      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
            <TableCell>Source</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Latency (ms)</TableCell>
            <TableCell>Error %</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {apisData.map(api => (
            <TableRow key={api.id}>
              <TableCell>{api.name}</TableCell>
              <TableCell>{api.source}</TableCell>
              <TableCell>{api.status}</TableCell>
              <TableCell>{api.latency}</TableCell>
              <TableCell>{api.error}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </>
  );
};

export default APIs;
