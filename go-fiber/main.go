package main

import (
	"database/sql"
	"log"
	"os"
	"strconv"

	"github.com/gofiber/fiber/v2"
	_ "github.com/lib/pq"
)

type SpatialRef struct {
	Srid      int64   `json:"srid"`
	AuthName  *string `json:"auth_name"`
	AuthSrid  *int64  `json:"auth_srid"`
	Srtext    *string `json:"srtext"`
	Proj4text *string `json:"proj4text"`
}

var cachedRecords []SpatialRef

const query = "SELECT srid, auth_name, auth_srid, srtext, proj4text FROM spatial_ref_sys LIMIT $1"

func main() {
	db, err := sql.Open("postgres", os.Getenv("DATABASE_URL"))
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	db.SetMaxOpenConns(50)
	db.SetMaxIdleConns(10)

	// Warm cache used by the static mode
	if err := loadCache(db, 100); err != nil {
		log.Fatal(err)
	}

	app := fiber.New()

	app.Get("/spatial_ref_sys", func(c *fiber.Ctx) error {
		if c.Query("static") == "1" {
			return c.JSON(cachedRecords)
		}

		limit := parseLimit(c.Query("limit"), 100)
		rows, err := db.Query(query, limit)
		if err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
		}
		defer rows.Close()

		results := make([]SpatialRef, 0, limit)
		for rows.Next() {
			var r SpatialRef
			if err := rows.Scan(&r.Srid, &r.AuthName, &r.AuthSrid, &r.Srtext, &r.Proj4text); err != nil {
				return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
			}
			results = append(results, r)
		}
		if err := rows.Err(); err != nil {
			return c.Status(fiber.StatusInternalServerError).SendString(err.Error())
		}
		return c.JSON(results)
	})

	port := os.Getenv("GO_FIBER_PORT")
	if port == "" {
		port = "8004"
	}
	log.Fatal(app.Listen(":" + port))
}

func loadCache(db *sql.DB, limit int) error {
	rows, err := db.Query(query, limit)
	if err != nil {
		return err
	}
	defer rows.Close()

	cachedRecords = make([]SpatialRef, 0, limit)
	for rows.Next() {
		var r SpatialRef
		if err := rows.Scan(&r.Srid, &r.AuthName, &r.AuthSrid, &r.Srtext, &r.Proj4text); err != nil {
			return err
		}
		cachedRecords = append(cachedRecords, r)
	}
	return rows.Err()
}

func parseLimit(s string, fallback int) int {
	if s == "" {
		return fallback
	}
	n, err := strconv.Atoi(s)
	if err != nil {
		return fallback
	}
	if n < 1 {
		return 1
	}
	if n > 1000 {
		return 1000
	}
	return n
}
