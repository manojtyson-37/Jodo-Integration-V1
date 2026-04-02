const API_DATA = {
    "Payment APIs": [
        { 
            name: "Create Order", 
            method: "POST", 
            endpoint: "/api/v1/integrations/pay/orders", 
            body: {
                "name": "Customer Name",
                "phone": "9876543210",
                "email": "you@example.com",
                "details": [
                    {
                        "component_type": "Payable Amount",
                        "amount": 1000.0
                    }
                ],
                "callback_url": "https://example.com/order-status"
            }
        },
        { 
            name: "Get Order Details", 
            method: "GET", 
            endpoint: "/api/v1/integrations/pay/orders/:id", 
            body: null 
        }
    ],
    "Simulation Utility": [
        {
            name: "Trigger Manual Webhook",
            method: "POST",
            endpoint: "/api/v1/webhooks/trigger",
            body: { event: "order.payment.debited", order_id: "order_mock_123" }
        }
    ]
};

document.addEventListener('DOMContentLoaded', () => {
    const apiList = document.getElementById('api-list');
    const editor = document.getElementById('json-editor');
    const responseBody = document.getElementById('response-body');
    const runBtn = document.getElementById('run-btn');
    const copyCurlBtn = document.getElementById('copy-curl-btn');
    const endpointDisplay = document.getElementById('endpoint-display');

    // Populate API List
    // ... (Existing population logic remains same)
    Object.keys(API_DATA).forEach(group => {
        const groupTitle = document.createElement('div');
        groupTitle.className = 'api-group-title';
        groupTitle.textContent = group;
        apiList.appendChild(groupTitle);

        API_DATA[group].forEach(api => {
            const item = document.createElement('div');
            item.className = 'api-item';
            item.innerHTML = `<span class="method-tag method-${api.method.toLowerCase()}">${api.method}</span> ${api.name}`;
            item.onclick = () => selectAPI(api, item);
            apiList.appendChild(item);
        });
    });

    function selectAPI(api, element) {
        document.querySelectorAll('.api-item').forEach(el => el.classList.remove('active'));
        element.classList.add('active');
        endpointDisplay.textContent = api.endpoint;
        editor.value = api.body ? JSON.stringify(api.body, null, 4) : '';
        responseBody.textContent = '// Send request to see real-time response';
    }

    // Copy Curl Functionality
    copyCurlBtn.onclick = () => {
        const user = JSON.parse(localStorage.getItem('jodo_user') || '{}');
        const apiItem = document.querySelector('.api-item.active');
        if (!apiItem) {
            alert("Select an API first");
            return;
        }

        const endpoint = endpointDisplay.textContent;
        const method = apiItem.querySelector('.method-tag').textContent;
        const bodyContent = editor.value;
        const authString = `${user.sandbox_key || 'YOUR_KEY'}:${user.sandbox_secret || 'YOUR_SECRET'}`;
        
        // Dynamic URL based on current host to ensure CURL is runnable
        const baseUrl = window.location.origin;
        const url = `${baseUrl}${endpoint}`;

        let curlCmd = `curl --location 'https://${authString}@${baseUrl.replace('https://', '')}${endpoint}' \\\n`;
        curlCmd += `--header 'Content-Type: application/json' \\\n`;
        curlCmd += `--header 'X-PG: jodo' \\\n`;
        
        if (method !== 'GET' && bodyContent) {
            curlCmd += `--data-raw '${bodyContent.replace(/'/g, "'\\''")}'`;
        }

        navigator.clipboard.writeText(curlCmd).then(() => {
            showToast("🚀 Curl Command Copied!");
        }).catch(err => {
            console.error('Failed to copy: ', err);
            alert("Failed to copy to clipboard");
        });
    };

    runBtn.onclick = async () => {
        const user = JSON.parse(localStorage.getItem('jodo_user') || '{}');
        const pg = 'jodo';
        const apiItem = document.querySelector('.api-item.active');
        if (!apiItem) return;

        const endpoint = endpointDisplay.textContent;
        const method = apiItem.querySelector('.method-tag').textContent;

        runBtn.disabled = true;
        runBtn.textContent = '⏳ Sending...';
        responseBody.textContent = `→ ${method} ${endpoint}\n\nConnecting to Jodo Sandbox...`;

        try {
            let body = editor.value ? JSON.parse(editor.value) : null;
            let url = endpoint;
            
            if (url.includes(':id')) {
                const id = prompt("Enter Order ID:");
                if (!id) throw new Error("Order ID is required");
                url = url.replace(':id', id);
            }

            const headers = { 
                'Content-Type': 'application/json', 
                'X-PG': pg,
                'X-Jodo-Session-Email': USER_DATA.email || '',
                'Authorization': 'Basic ' + btoa((USER_DATA.sandbox_key || '') + ':')
            };

            const fetchOptions = { method, headers };
            if (body && method !== 'GET') fetchOptions.body = JSON.stringify(body);

            const res = await fetch(url, fetchOptions);
            const data = await res.json();
            
            responseBody.textContent = JSON.stringify(data, null, 4);

            if (url.includes('/orders') && method === 'POST' && data?.data?.payment_url) {
                showToast(data.data.payment_url, true); // true for payment link
            }

        } catch (err) {
            responseBody.textContent = `❌ Error: ${err.message}`;
        } finally {
            runBtn.disabled = false;
            runBtn.textContent = '▶ Send Request';
        }
    };
});

function showToast(message, isPayment = false) {
    const toast = document.createElement('div');
    toast.style = "position: fixed; bottom: 30px; right: 30px; background: #6366f1; color: white; padding: 15px 25px; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); z-index: 1000; display: flex; align-items: center; gap: 15px; transition: opacity 0.3s ease;";
    
    if (isPayment) {
        toast.innerHTML = `
            <div style="font-size: 0.9rem;"><b>✅ Order Created!</b><br>Continue to simulated checkout.</div>
            <button onclick="window.open('${message}', '_blank')" style="background: white; color: #6366f1; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 700;">Open Checkout</button>
        `;
    } else {
        toast.innerHTML = `<div style="font-size: 0.9rem;"><b>${message}</b></div>`;
    }
    
    document.body.appendChild(toast);
    setTimeout(() => { toast.style.opacity = '0'; setTimeout(() => toast.remove(), 300); }, isPayment ? 8000 : 3000);
}
