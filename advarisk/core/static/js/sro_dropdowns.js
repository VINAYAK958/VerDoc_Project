document.addEventListener("DOMContentLoaded", function() {
    const stateSelect = document.querySelector('.sro-state');
    const districtSelect = document.querySelector('.sro-district');
    const subDistrictSelect = document.querySelector('.sro-sub-district');
    const sroSelect = document.querySelector('.sro-node');

    if (!stateSelect) return;

    function populateSelect(selectEl, dataList, defaultOptionStr) {
        selectEl.innerHTML = `<option value="">${defaultOptionStr}</option>`;
        dataList.forEach(item => {
            const opt = document.createElement('option');
            opt.value = item;
            opt.textContent = item;
            selectEl.appendChild(opt);
        });
    }

    // Initialize all lower selects with a default option waiting logic
    if(!stateSelect.value) {
        districtSelect.innerHTML = '<option value="">--- Select District ---</option>';
        subDistrictSelect.innerHTML = '<option value="">--- Select Sub-District ---</option>';
        sroSelect.innerHTML = '<option value="">--- Select SRO ---</option>';
    }

    // Fetch States IF it's not already pre-populated (like during an edit)
    fetch('/api/locations/states/')
        .then(r => r.json())
        .then(data => {
            // Re-populate preserving current state if it exists
            const currentVal = stateSelect.value;
            populateSelect(stateSelect, data.states, '--- Select State ---');
            if (currentVal) stateSelect.value = currentVal;
        });

    stateSelect.addEventListener('change', function() {
        districtSelect.innerHTML = '<option value="">--- Select District ---</option>';
        subDistrictSelect.innerHTML = '<option value="">--- Select Sub-District ---</option>';
        sroSelect.innerHTML = '<option value="">--- Select SRO ---</option>';
        
        if (this.value) {
            fetch(`/api/locations/districts/?state=${encodeURIComponent(this.value)}`)
                .then(r => r.json())
                .then(data => populateSelect(districtSelect, data.districts, '--- Select District ---'));
        }
    });

    districtSelect.addEventListener('change', function() {
        subDistrictSelect.innerHTML = '<option value="">--- Select Sub-District ---</option>';
        sroSelect.innerHTML = '<option value="">--- Select SRO ---</option>';
        
        if (this.value) {
            fetch(`/api/locations/sub_districts/?state=${encodeURIComponent(stateSelect.value)}&district=${encodeURIComponent(this.value)}`)
                .then(r => r.json())
                .then(data => populateSelect(subDistrictSelect, data.sub_districts, '--- Select Sub-District ---'));
        }
    });

    subDistrictSelect.addEventListener('change', function() {
        sroSelect.innerHTML = '<option value="">--- Select SRO ---</option>';
        
        if (this.value) {
            fetch(`/api/locations/sro_nos/?state=${encodeURIComponent(stateSelect.value)}&district=${encodeURIComponent(districtSelect.value)}&sub_district=${encodeURIComponent(this.value)}`)
                .then(r => r.json())
                .then(data => populateSelect(sroSelect, data.sro_nos, '--- Select SRO ---'));
        }
    });
});
