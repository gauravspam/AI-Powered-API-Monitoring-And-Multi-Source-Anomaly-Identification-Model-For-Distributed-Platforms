package main.java.com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.AlertRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;
import java.util.UUID;

public interface AlertRepository extends JpaRepository<AlertRecord, UUID> {
    List<AlertRecord> findByEnabled(boolean enabled);
    List<AlertRecord> findByAlertName(String alertName);
}