package main.java.com.api.monitoring.backend.repository;

import com.api.monitoring.backend.model.AlertRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface AlertRepository extends JpaRepository<AlertRecord, Long> {
    List<AlertRecord> findByEnabled(boolean enabled);
    List<AlertRecord> findByAlertName(String alertName);
}