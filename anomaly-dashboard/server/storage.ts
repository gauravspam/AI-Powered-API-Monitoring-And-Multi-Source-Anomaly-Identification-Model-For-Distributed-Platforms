import { drizzle } from "drizzle-orm/better-sqlite3";
import Database from "better-sqlite3";
import * as schema from "@shared/schema";
import { eq, desc } from "drizzle-orm";

const sqlite = new Database("sqlite.db");
const db = drizzle(sqlite, { schema });

// Create tables
sqlite.exec(`
  CREATE TABLE IF NOT EXISTS simulations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    metrics_count INTEGER NOT NULL DEFAULT 0,
    logs_count INTEGER NOT NULL DEFAULT 0,
    traces_count INTEGER NOT NULL DEFAULT 0,
    severity TEXT NOT NULL DEFAULT 'MEDIUM',
    status TEXT NOT NULL DEFAULT 'pending',
    response_payload TEXT,
    hybrid_score REAL,
    msif_score REAL,
    ple_score REAL,
    final_severity TEXT,
    error TEXT
  )
`);

export interface IStorage {
  createSimulation(data: schema.InsertSimulation): schema.Simulation;
  getSimulations(limit?: number): schema.Simulation[];
  updateSimulation(id: number, data: Partial<schema.Simulation>): schema.Simulation | undefined;
}

export class Storage implements IStorage {
  createSimulation(data: schema.InsertSimulation): schema.Simulation {
    return db.insert(schema.simulations).values(data).returning().get() as schema.Simulation;
  }

  getSimulations(limit = 50): schema.Simulation[] {
    return db.select().from(schema.simulations).orderBy(desc(schema.simulations.id)).limit(limit).all();
  }

  updateSimulation(id: number, data: Partial<schema.Simulation>): schema.Simulation | undefined {
    return db.update(schema.simulations)
      .set(data)
      .where(eq(schema.simulations.id, id))
      .returning()
      .get() as schema.Simulation | undefined;
  }
}

export const storage = new Storage();
