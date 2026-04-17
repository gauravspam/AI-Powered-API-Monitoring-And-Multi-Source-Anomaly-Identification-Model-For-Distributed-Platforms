import { sqliteTable, text, integer, real } from "drizzle-orm/sqlite-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Simulation history for Signal Simulator
export const simulations = sqliteTable("simulations", {
  id: integer("id").primaryKey({ autoIncrement: true }),
  timestamp: text("timestamp").notNull(),
  metricsCount: integer("metrics_count").notNull().default(0),
  logsCount: integer("logs_count").notNull().default(0),
  tracesCount: integer("traces_count").notNull().default(0),
  severity: text("severity").notNull().default("MEDIUM"),
  status: text("status").notNull().default("pending"),
  responsePayload: text("response_payload"),
  hybridScore: real("hybrid_score"),
  msifScore: real("msif_score"),
  pleScore: real("ple_score"),
  finalSeverity: text("final_severity"),
  error: text("error"),
});

export const insertSimulationSchema = createInsertSchema(simulations).omit({ id: true });
export type InsertSimulation = z.infer<typeof insertSimulationSchema>;
export type Simulation = typeof simulations.$inferSelect;
