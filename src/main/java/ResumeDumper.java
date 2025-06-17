package com.company.resume;

import java.io.File;
import java.io.IOException;
import java.nio.file.*;
import java.sql.*;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.PDFTextStripper;
import io.github.cdimascio.dotenv.Dotenv;

public class ResumeDumper {

    static final String DB_URL = "jdbc:mysql://localhost:3306/company";
    static final String USER = "root";
    static final String PASS = System.getenv("DB_PASSWORD");

    public static void main(String[] args) {
        String folderPath = System.getenv("RESUME_SOURCE");

        try (Connection conn = DriverManager.getConnection(DB_URL, USER, PASS)) {
            Files.list(Paths.get(folderPath))
                    .filter(path -> path.toString().endsWith(".pdf"))
                    .forEach(file -> {
                        try {
                            String content = extractTextFromPDF(file.toFile());
                            insertResume(conn, file.getFileName().toString(), content);
                            System.out.println("Imported: " + file.getFileName());
                        } catch (Exception e) {
                            System.err.println("Failed to process " + file.getFileName());
                            e.printStackTrace();
                        }
                    });
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    static String extractTextFromPDF(File file) throws IOException {
        try (PDDocument document = PDDocument.load(file)) {
            return new PDFTextStripper().getText(document);
        }
    }

    static void insertResume(Connection conn, String filename, String content) throws SQLException {
        String sql = "INSERT INTO employee_resumes (filename, content) VALUES (?, ?)";
        try (PreparedStatement stmt = conn.prepareStatement(sql)) {
            stmt.setString(1, filename);
            stmt.setString(2, content);
            stmt.executeUpdate();
        }
    }
}
