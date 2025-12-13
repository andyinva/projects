# Duplicate File Finder and Remover
# PowerShell script with GUI for finding and deleting duplicate files

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Function to calculate file hash
function Get-FileHashMD5 {
    param([string]$FilePath)
    try {
        $hash = Get-FileHash -Path $FilePath -Algorithm MD5
        return $hash.Hash
    }
    catch {
        return $null
    }
}

# Function to find duplicate files
function Find-Duplicates {
    param([string]$Path)

    $statusLabel.Text = "Scanning for files..."
    [System.Windows.Forms.Application]::DoEvents()

    # Get all files in current directory
    $files = Get-ChildItem -Path $Path -File -Recurse -ErrorAction SilentlyContinue

    $statusLabel.Text = "Analyzing $($files.Count) files..."
    [System.Windows.Forms.Application]::DoEvents()

    # Group files by name and size
    $duplicates = @()

    # Group by size first (faster)
    $sizeGroups = $files | Group-Object -Property Length | Where-Object { $_.Count -gt 1 }

    foreach ($sizeGroup in $sizeGroups) {
        # Within same size, group by base name similarity
        $nameGroups = $sizeGroup.Group | Group-Object -Property Name

        foreach ($nameGroup in $nameGroups) {
            if ($nameGroup.Count -gt 1) {
                # Exact name matches with same size - verify with hash
                $hashGroups = $nameGroup.Group | Group-Object -Property { Get-FileHashMD5 $_.FullName }

                foreach ($hashGroup in $hashGroups) {
                    if ($hashGroup.Count -gt 1) {
                        # Keep first file, mark rest as duplicates
                        $original = $hashGroup.Group[0]
                        for ($i = 1; $i -lt $hashGroup.Group.Count; $i++) {
                            $duplicates += [PSCustomObject]@{
                                File = $hashGroup.Group[$i]
                                DuplicateOf = $original.FullName
                                Reason = "Exact duplicate (same name, size, content)"
                                Size = $hashGroup.Group[$i].Length
                            }
                        }
                    }
                }
            }
        }
    }

    # Also check for similar filenames with same size and content
    foreach ($sizeGroup in $sizeGroups) {
        $filesInGroup = $sizeGroup.Group

        for ($i = 0; $i -lt $filesInGroup.Count; $i++) {
            for ($j = $i + 1; $j -lt $filesInGroup.Count; $j++) {
                $file1 = $filesInGroup[$i]
                $file2 = $filesInGroup[$j]

                # Skip if already marked as duplicate
                if ($duplicates.File.FullName -contains $file2.FullName) {
                    continue
                }

                # Check if names are similar (version numbers, copy indicators)
                $name1 = [System.IO.Path]::GetFileNameWithoutExtension($file1.Name)
                $name2 = [System.IO.Path]::GetFileNameWithoutExtension($file2.Name)

                # Check for common patterns: "file (1)", "file_v2", "file - Copy", etc.
                $pattern1 = $name1 -replace '\s*\(\d+\)|\s*-\s*Copy|\s*_v?\d+|_\d+$', ''
                $pattern2 = $name2 -replace '\s*\(\d+\)|\s*-\s*Copy|\s*_v?\d+|_\d+$', ''

                if ($pattern1 -eq $pattern2 -and $file1.Extension -eq $file2.Extension) {
                    # Same base name and size, verify with hash
                    $hash1 = Get-FileHashMD5 $file1.FullName
                    $hash2 = Get-FileHashMD5 $file2.FullName

                    if ($hash1 -eq $hash2 -and $null -ne $hash1) {
                        $duplicates += [PSCustomObject]@{
                            File = $file2
                            DuplicateOf = $file1.FullName
                            Reason = "Version/Copy duplicate (similar name, same size, same content)"
                            Size = $file2.Length
                        }
                    }
                }
            }
        }
    }

    $statusLabel.Text = "Found $($duplicates.Count) potential duplicates"
    return $duplicates
}

# Create main form
$form = New-Object System.Windows.Forms.Form
$form.Text = "Duplicate File Finder"
$form.Size = New-Object System.Drawing.Size(900, 600)
$form.StartPosition = "CenterScreen"
$form.MinimumSize = New-Object System.Drawing.Size(800, 500)

# Create status label
$statusLabel = New-Object System.Windows.Forms.Label
$statusLabel.Location = New-Object System.Drawing.Point(10, 10)
$statusLabel.Size = New-Object System.Drawing.Size(860, 20)
$statusLabel.Text = "Click 'Scan' to find duplicates in current directory"
$form.Controls.Add($statusLabel)

# Create ListView for displaying files
$listView = New-Object System.Windows.Forms.ListView
$listView.Location = New-Object System.Drawing.Point(10, 40)
$listView.Size = New-Object System.Drawing.Size(860, 450)
$listView.View = [System.Windows.Forms.View]::Details
$listView.CheckBoxes = $true
$listView.FullRowSelect = $true
$listView.GridLines = $true
$listView.Anchor = "Top,Left,Right,Bottom"

# Add columns
$listView.Columns.Add("File Path", 350) | Out-Null
$listView.Columns.Add("Size (KB)", 100) | Out-Null
$listView.Columns.Add("Duplicate Of", 250) | Out-Null
$listView.Columns.Add("Reason", 180) | Out-Null

$form.Controls.Add($listView)

# Create Scan button
$scanButton = New-Object System.Windows.Forms.Button
$scanButton.Location = New-Object System.Drawing.Point(10, 500)
$scanButton.Size = New-Object System.Drawing.Size(100, 30)
$scanButton.Text = "Scan"
$scanButton.Anchor = "Bottom,Left"
$scanButton.Add_Click({
    $listView.Items.Clear()
    $currentPath = Get-Location
    $duplicates = Find-Duplicates -Path $currentPath

    foreach ($dup in $duplicates) {
        $item = New-Object System.Windows.Forms.ListViewItem($dup.File.FullName)
        $item.SubItems.Add([math]::Round($dup.Size / 1KB, 2).ToString()) | Out-Null
        $item.SubItems.Add($dup.DuplicateOf) | Out-Null
        $item.SubItems.Add($dup.Reason) | Out-Null
        $item.Tag = $dup.File.FullName
        $listView.Items.Add($item) | Out-Null
    }

    if ($duplicates.Count -eq 0) {
        [System.Windows.Forms.MessageBox]::Show("No duplicates found!", "Scan Complete",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information)
    }
})
$form.Controls.Add($scanButton)

# Create Select All button
$selectAllButton = New-Object System.Windows.Forms.Button
$selectAllButton.Location = New-Object System.Drawing.Point(120, 500)
$selectAllButton.Size = New-Object System.Drawing.Size(100, 30)
$selectAllButton.Text = "Select All"
$selectAllButton.Anchor = "Bottom,Left"
$selectAllButton.Add_Click({
    foreach ($item in $listView.Items) {
        $item.Checked = $true
    }
})
$form.Controls.Add($selectAllButton)

# Create Deselect All button
$deselectAllButton = New-Object System.Windows.Forms.Button
$deselectAllButton.Location = New-Object System.Drawing.Point(230, 500)
$deselectAllButton.Size = New-Object System.Drawing.Size(100, 30)
$deselectAllButton.Text = "Deselect All"
$deselectAllButton.Anchor = "Bottom,Left"
$deselectAllButton.Add_Click({
    foreach ($item in $listView.Items) {
        $item.Checked = $false
    }
})
$form.Controls.Add($deselectAllButton)

# Create Delete button
$deleteButton = New-Object System.Windows.Forms.Button
$deleteButton.Location = New-Object System.Drawing.Point(670, 500)
$deleteButton.Size = New-Object System.Drawing.Size(100, 30)
$deleteButton.Text = "Delete Selected"
$deleteButton.Anchor = "Bottom,Right"
$deleteButton.BackColor = [System.Drawing.Color]::IndianRed
$deleteButton.ForeColor = [System.Drawing.Color]::White
$deleteButton.Add_Click({
    $checkedItems = $listView.CheckedItems

    if ($checkedItems.Count -eq 0) {
        [System.Windows.Forms.MessageBox]::Show("No files selected for deletion.", "Warning",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Warning)
        return
    }

    $totalSize = 0
    foreach ($item in $checkedItems) {
        $totalSize += [double]$item.SubItems[1].Text
    }

    $result = [System.Windows.Forms.MessageBox]::Show(
        "Are you sure you want to delete $($checkedItems.Count) file(s)?`n`nTotal size: $([math]::Round($totalSize, 2)) KB`n`nThis action cannot be undone!",
        "Confirm Deletion",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Warning)

    if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
        $deleted = 0
        $failed = 0

        foreach ($item in $checkedItems) {
            try {
                Remove-Item -Path $item.Tag -Force -ErrorAction Stop
                $listView.Items.Remove($item)
                $deleted++
            }
            catch {
                $failed++
                Write-Host "Failed to delete: $($item.Tag) - $($_.Exception.Message)"
            }
        }

        $statusLabel.Text = "Deleted $deleted file(s). Failed: $failed"

        [System.Windows.Forms.MessageBox]::Show(
            "Deletion complete!`n`nDeleted: $deleted`nFailed: $failed",
            "Deletion Complete",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information)
    }
})
$form.Controls.Add($deleteButton)

# Create Exit button
$exitButton = New-Object System.Windows.Forms.Button
$exitButton.Location = New-Object System.Drawing.Point(780, 500)
$exitButton.Size = New-Object System.Drawing.Size(100, 30)
$exitButton.Text = "Exit"
$exitButton.Anchor = "Bottom,Right"
$exitButton.Add_Click({
    $form.Close()
})
$form.Controls.Add($exitButton)

# Show the form
$form.Add_Shown({$form.Activate()})
[void]$form.ShowDialog()
