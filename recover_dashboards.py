
import os
import re

# Define the exact valid script content for Admin Dashboard
# We use raw strings to avoid escaping issues
admin_script = r"""
    <script>
        function adminSystem() {
            return {
                currentTab: 'overview',
                adminName: '{{ current_user.name }}',
                adminRole: '{{ current_user.role }}',
                
                // Modals
                showAddAdminModal: false,
                showAddHospModal: false,
                showAddAmbModal: false,
                showAlertModal: false,
                
                // Alerts & Notifications
                targetPharma: { shop_name: '' },
                alertMsg: '',
                alertType: 'info',
                scanning: false,
                scanResults: [],
                
                // Search & Filter
                search: '',
                medicineSearch: '',
                pharmacyFilterSnippet: '', // For viewing stock of specific pharmacy
                
                // DATA INJECTION
                pharmacies: {{ pharmacies_json | safe }},
                subAdmins: {{ sub_admins_json | safe }},
                hospitals: {{ hospitals_json | safe }},
                medicines: {{ medicines_json | safe }},
                ambulances: {{ ambulances_json | safe }},
                recentSOS: {{ emergencies_json | safe }},

                stats: {
                    pharmacies: {{ pharmacies_count }},
                    hospitals: {{ hospitals_count }},
                    medicines: {{ medicines_count }},
                    ambulances: {{ ambulances_count }}
                },

                tabs: [
                    { id: 'overview', name: 'Control Center', icon: 'fas fa-grid-2' },
                    { id: 'pharmacies', name: 'Pharmacy Network', icon: 'fas fa-store' },
                    { id: 'medicines', name: 'Master Inventory', icon: 'fas fa-pills' },
                    { id: 'ambulances', name: 'Rescue Fleet', icon: 'fas fa-truck-medical' },
                    { id: 'sos', name: 'Emergency Feed', icon: 'fas fa-broadcast-tower' },
                    { id: 'admins', name: 'Access Control', icon: 'fas fa-user-shield' },
                    { id: 'alerts', name: 'Network Audit', icon: 'fas fa-clipboard-check' },
                ],

                init() {
                    console.log('MedLink Control Center Online');
                },

                // Getters
                get pendingCount() {
                    return this.pharmacies.filter(p => !p.verified).length;
                },

                get expiringCount() {
                    return this.medicines.filter(m => this.isNearExpiry(m.expiry)).length;
                },

                get filteredPharmacies() {
                    if (!this.search) return this.pharmacies;
                    const q = this.search.toLowerCase();
                    return this.pharmacies.filter(p => 
                        p.shop_name.toLowerCase().includes(q) || 
                        (p.dl_no && p.dl_no.toLowerCase().includes(q))
                    );
                },

                get filteredMedicines() {
                    let list = this.medicines;
                    if (this.pharmacyFilterSnippet) {
                        list = list.filter(m => m.pharmacy_name === this.pharmacyFilterSnippet);
                    }
                    if (this.medicineSearch) {
                        const q = this.medicineSearch.toLowerCase();
                        list = list.filter(m => 
                            m.name.toLowerCase().includes(q) || 
                            m.pharmacy_name.toLowerCase().includes(q)
                        );
                    }
                    return list;
                },

                get filteredSOS() {
                    return this.recentSOS;
                },

                // Core Methods
                isNearExpiry(date) {
                    const d = new Date(date);
                    const today = new Date();
                    const diff = (d - today) / (1000 * 60 * 60 * 24);
                    return diff < 30;
                },

                viewPharmacyStock(name) {
                    this.pharmacyFilterSnippet = name;
                    this.medicineSearch = '';
                    this.currentTab = 'medicines';
                },

                // Action API Calls
                async verifyPharma(id) {
                    const res = await fetch(`/admin/verify_pharmacy/${id}`);
                    if (res.ok) location.reload();
                },

                async deletePharma(id) {
                    if (confirm('Permanently remove this pharmacy?')) {
                        const res = await fetch(`/admin/reject_pharmacy/${id}`);
                        if (res.ok) location.reload();
                    }
                },

                async deleteMedicine(id) {
                    if (confirm('Remove this medicine from system?')) {
                        const res = await fetch(`/admin/delete_medicine/${id}`);
                        if (res.ok) location.reload();
                    }
                },

                async deleteAmbulance(id) {
                    if (confirm('Decommission this unit?')) {
                        const res = await fetch(`/admin/delete_ambulance/${id}`);
                        if (res.ok) location.reload();
                    }
                },

                async deleteAdmin(id) {
                    if (confirm('Revoke access for this sub-admin?')) {
                        const res = await fetch(`/admin/remove_sub_admin/${id}`);
                        if (res.ok) location.reload();
                    }
                },

                async resolveSOS(id) {
                    const res = await fetch(`/admin/resolve_broadcast/${id}`, { method: 'POST' });
                    if (res.ok) location.reload();
                },

                // Messaging System
                openAlertModal(pharma) {
                    this.targetPharma = pharma;
                    this.alertMsg = '';
                    this.showAlertModal = true;
                },

                async submitAlert() {
                    const res = await fetch('/admin/send_alert', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            pharmacy_id: this.targetPharma.id,
                            message: this.alertMsg,
                            type: this.alertType
                        })
                    });
                    if (res.ok) {
                        this.showAlertModal = false;
                        alert('Alert pushed to pharmacy terminal.');
                    }
                },

                // Global Scan
                async scanAndAlert() {
                    this.scanning = true;
                    this.scanResults = [];
                    
                    const nearExpiry = this.medicines.filter(m => this.isNearExpiry(m.expiry));
                    
                    for (const m of nearExpiry) {
                        this.scanResults.push({
                            med: m.name,
                            pharma: m.pharmacy_name,
                            pharma_id: m.pharmacy_id,
                            expiry: m.expiry
                        });
                        
                        // Send auto-alert
                        await fetch('/admin/send_alert', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                pharmacy_id: m.pharmacy_id,
                                message: `CRITICAL: Item "${m.name}" is expiring on ${m.expiry}. Please audit stock.`,
                                type: 'danger'
                            })
                        });
                    }
                    
                    this.scanning = false;
                    alert('Scan complete. Expiry notifications broadcasted.');
                }
            };
        }
    </script>
"""

# Define the exact valid script content for Pharmacy Dashboard
pharmacy_script = r"""
    <script>
        function pharmacyApp() {
            return {
                form: { name: '', manufacturer: '', description: '', qty: '', price: '', expiry: '' },
                
                // DATA INJECTION
                inventory: {{ inventory_json | safe }},
                alerts: {{ alerts_json | safe }},
                emergencies: {{ emergencies_json | safe }},

                init() {
                    console.log('Pharmacy Terminal Online');
                },

                simulateBroadcast() {
                    alert("Emergency Broadcast system active. Monitoring SOS requests...");
                },

                async addStock() {
                    const res = await fetch('/pharmacy/add_stock', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(this.form)
                    });
                    if (res.ok) location.reload();
                    else alert("Failed to add stock");
                },

                async removeStock(id) {
                    if (confirm('Delete this item?')) {
                        const res = await fetch(`/pharmacy/remove_stock/${id}`, { method: 'POST' });
                        if (res.ok) location.reload();
                    }
                },

                isExpiring(date) {
                    const d = new Date(date);
                    const today = new Date();
                    const diff = (d - today) / (1000 * 60 * 60 * 24);
                    return diff < 30;
                }
            }
        }
    </script>
"""

def fix_file(file_path, script_content):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the script block
    # We use a non-greedy dotsall regex to find the last script block before body ends
    new_content = re.sub(r'<script>.*?</script>', script_content, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Fixed: {file_path}")

# Run fixes
fix_file(r"c:\Users\eldho\Downloads\Templatefolder\templates\admin_dashboard.html", admin_script)
fix_file(r"c:\Users\eldho\Downloads\Templatefolder\templates\pharmacy.html", pharmacy_script)
