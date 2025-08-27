"""
Integration tests for data persistence functionality.

This module tests the complete data persistence workflow including
encryption, repository operations, and backup management.
"""

import pytest
import tempfile
import time
from pathlib import Path

from src.core.macro_data import (
    MacroRecording,
    create_mouse_click_operation,
    create_key_operation,
)
from src.core.macro_data import MouseButton, Position
from src.data.repositories.file_system_macro_repository import FileSystemMacroRepository
from src.data.encryption.encryption_service import (
    EncryptionService,
    PasswordValidationError,
)
from src.data.backup.backup_manager import BackupManager
from src.data.repositories.macro_repository import (
    CorruptedFileError,
    InvalidPasswordError as RepoInvalidPasswordError,
)


class TestDataPersistenceIntegration:
    """Integration tests for complete data persistence workflow."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def sample_recording(self):
        """Create sample macro recording for testing."""
        recording = MacroRecording(
            name='Test Macro',
            created_at=time.time(),
            operations=[],
            metadata={'test': True},
        )

        # Add some sample operations
        recording.add_operation(
            create_mouse_click_operation(
                MouseButton.LEFT, Position(100, 200), time.time()
            )
        )

        recording.add_operation(
            create_key_operation('a', 'press', ['ctrl'], time.time() + 1)
        )

        return recording

    @pytest.fixture
    def repository(self):
        """Create file system repository for testing."""
        return FileSystemMacroRepository()

    @pytest.fixture
    def encryption_service(self):
        """Create encryption service for testing."""
        return EncryptionService()

    @pytest.fixture
    def backup_manager(self):
        """Create backup manager for testing."""
        return BackupManager(max_backups=3)

    def test_complete_save_load_workflow(self, temp_dir, sample_recording, repository):
        """Test complete save and load workflow with encryption."""
        file_path = temp_dir / 'test_macro.gma.json'
        password = 'testpassword123'

        # Save the recording
        success = repository.save(sample_recording, file_path, password)
        assert success is True
        assert file_path.exists()

        # Load the recording
        loaded_recording = repository.load(file_path, password)

        # Verify loaded data
        assert loaded_recording.name == sample_recording.name
        assert loaded_recording.operation_count == sample_recording.operation_count
        assert len(loaded_recording.operations) == 2

        # Verify first operation (mouse click)
        first_op = loaded_recording.operations[0]
        assert first_op.mouse_op is not None
        assert first_op.mouse_op.button == MouseButton.LEFT
        assert first_op.mouse_op.position.x == 100
        assert first_op.mouse_op.position.y == 200

        # Verify second operation (key press)
        second_op = loaded_recording.operations[1]
        assert second_op.keyboard_op is not None
        assert second_op.keyboard_op.key == 'a'
        assert second_op.keyboard_op.action == 'press'
        assert 'ctrl' in second_op.keyboard_op.modifiers

    def test_encryption_service_functionality(self, encryption_service):
        """Test encryption service encrypt/decrypt functionality."""
        test_data = {'name': 'Test Data', 'value': 42, 'nested': {'key': 'value'}}
        password = 'securepassword'

        # Encrypt data
        encrypted_data = encryption_service.encrypt_data(test_data, password)
        assert isinstance(encrypted_data, bytes)
        assert len(encrypted_data) > 0

        # Decrypt data
        decrypted_data = encryption_service.decrypt_data(encrypted_data, password)
        assert decrypted_data == test_data

    def test_password_validation(self, encryption_service):
        """Test password validation functionality."""
        # Valid password
        assert encryption_service.validate_password('validpassword123')

        # Invalid passwords
        with pytest.raises(PasswordValidationError):
            encryption_service.validate_password('short')  # Too short

        with pytest.raises(PasswordValidationError):
            encryption_service.validate_password('')  # Empty

    def test_wrong_password_handling(self, temp_dir, sample_recording, repository):
        """Test handling of incorrect passwords."""
        file_path = temp_dir / 'test_macro.gma.json'
        correct_password = 'correctpassword'
        wrong_password = 'wrongpassword'

        # Save with correct password
        repository.save(sample_recording, file_path, correct_password)

        # Try to load with wrong password
        with pytest.raises(RepoInvalidPasswordError):
            repository.load(file_path, wrong_password)

    def test_backup_management_workflow(self, temp_dir, backup_manager):
        """Test backup creation and management."""
        # Create test file
        test_file = temp_dir / 'test_macro.gma.json'
        test_file.write_text('test content')

        # Create backup
        backup_path = backup_manager.create_backup(test_file)
        assert backup_path is not None
        assert backup_path.exists()

        # List backups
        backups = backup_manager.list_backups(test_file)

        # Debug: Check backup directory contents
        backup_dir = test_file.parent / '.backups'
        if backup_dir.exists():
            backup_files = list(backup_dir.glob('*'))
            print(f'Backup files found: {backup_files}')
            print(f'Backup path created: {backup_path}')

        assert len(backups) == 1
        assert backups[0].path == backup_path

        # Create more backups
        time.sleep(0.1)  # Ensure different timestamps
        backup_manager.create_backup(test_file)
        time.sleep(0.1)
        backup_manager.create_backup(test_file)

        backups = backup_manager.list_backups(test_file)
        assert len(backups) == 3

        # Test cleanup (max_backups = 3)
        time.sleep(0.1)
        backup_manager.create_backup(test_file)  # This should trigger cleanup

        backups = backup_manager.list_backups(test_file)
        assert len(backups) == 3  # Should still be 3 due to max limit

    def test_backup_restore_functionality(self, temp_dir, backup_manager):
        """Test backup restoration functionality."""
        # Create original file
        original_file = temp_dir / 'original.gma.json'
        original_content = 'original content'
        original_file.write_text(original_content)

        # Create backup
        backup_path = backup_manager.create_backup(original_file)

        # Modify original file
        modified_content = 'modified content'
        original_file.write_text(modified_content)

        # Restore from backup
        success = backup_manager.restore_backup(backup_path, original_file)
        assert success is True

        # Verify restoration
        restored_content = original_file.read_text()
        assert restored_content == original_content

    def test_repository_file_operations(self, temp_dir, repository, sample_recording):
        """Test repository file operations (exists, delete, list)."""
        file_path = temp_dir / 'test_macro.gma.json'
        password = 'testpassword'

        # Initially file should not exist
        assert not repository.exists(file_path)

        # Save file
        repository.save(sample_recording, file_path, password)

        # Now file should exist
        assert repository.exists(file_path)

        # List recordings in directory
        recordings = repository.list_recordings(temp_dir)
        assert len(recordings) == 1
        assert recordings[0] == file_path

        # Delete file
        success = repository.delete(file_path)
        assert success is True
        assert not repository.exists(file_path)

    def test_large_file_handling(self, temp_dir, repository):
        """Test handling of large macro files (performance test)."""
        # Create recording with many operations
        large_recording = MacroRecording(
            name='Large Test Macro', created_at=time.time(), operations=[], metadata={}
        )

        # Add 1000 operations
        for i in range(1000):
            large_recording.add_operation(
                create_mouse_click_operation(
                    MouseButton.LEFT,
                    Position(i % 1000, (i * 2) % 1000),
                    time.time() + i * 0.001,
                )
            )

        file_path = temp_dir / 'large_macro.gma.json'
        password = 'testpassword'

        # Measure save time
        start_time = time.time()
        success = repository.save(large_recording, file_path, password)
        save_time = time.time() - start_time

        assert success is True
        assert save_time < 5.0  # Should complete within 5 seconds

        # Measure load time
        start_time = time.time()
        loaded_recording = repository.load(file_path, password)
        load_time = time.time() - start_time

        assert load_time < 5.0  # Should complete within 5 seconds
        assert loaded_recording.operation_count == 1000

    def test_corrupted_file_handling(self, temp_dir, repository):
        """Test handling of corrupted files."""
        file_path = temp_dir / 'corrupted.gma.json'

        # Create corrupted file (invalid encrypted data)
        file_path.write_bytes(b'invalid encrypted data')

        with pytest.raises((CorruptedFileError, RepoInvalidPasswordError)):
            repository.load(file_path, 'anypassword')

    def test_concurrent_access_safety(self, temp_dir, sample_recording):
        """Test thread safety for concurrent file operations."""
        import threading

        file_path = temp_dir / 'concurrent_test.gma.json'
        password = 'testpassword'
        results = []
        errors = []

        def save_operation():
            try:
                repo = FileSystemMacroRepository()
                success = repo.save(sample_recording, file_path, password)
                results.append(success)
            except Exception as e:
                errors.append(e)

        def load_operation():
            try:
                repo = FileSystemMacroRepository()
                # Wait a bit to ensure file is saved first
                time.sleep(0.1)
                recording = repo.load(file_path, password)
                results.append(recording is not None)
            except Exception as e:
                errors.append(e)

        # Run concurrent operations
        threads = []
        threads.append(threading.Thread(target=save_operation))
        threads.append(threading.Thread(target=load_operation))

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Verify no errors and successful operations
        assert len(errors) == 0, f'Concurrent access errors: {errors}'
        assert len([r for r in results if r]) >= 1  # At least one successful operation

    def test_edge_case_filenames(self, temp_dir, repository, sample_recording):
        """Test handling of edge case filenames."""
        password = 'testpassword'

        # Test various filename patterns
        test_filenames = [
            'normal_file.gma.json',
            'file with spaces.gma.json',
            'file-with-dashes.gma.json',
            'file_with_unicode_テスト.gma.json',
        ]

        for filename in test_filenames:
            file_path = temp_dir / filename

            # Save and load
            success = repository.save(sample_recording, file_path, password)
            assert success, f'Failed to save file with name: {filename}'

            loaded = repository.load(file_path, password)
            assert loaded.name == sample_recording.name, (
                f'Failed to load file with name: {filename}'
            )
