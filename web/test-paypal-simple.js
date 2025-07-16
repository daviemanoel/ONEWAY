const https = require('https');

// Credenciais fornecidas pelo usuário
const CLIENT_ID = 'AZV4ztJGO93BrofKtimax5JhqR4vCw3OSyQouUNIhQselj_50f40ck8ft7bNctLazK9iW9fXPXG53dOp';
const CLIENT_SECRET = 'EBQmhC4lNgBrZufvBGtDWBBunBns10jnVp5TCAUrDVq9JY-NfPOV81xMzNfB1foa4EPqC5dYr3_aJ39i';

// Base64 encode das credenciais
const auth = Buffer.from(`${CLIENT_ID}:${CLIENT_SECRET}`).toString('base64');

console.log('🔍 Testando credenciais PayPal...');
console.log('Client ID:', CLIENT_ID);
console.log('Environment: 🟢 PRODUÇÃO (Live)');

// Função para fazer request HTTP
function makeRequest(options, postData = null) {
    return new Promise((resolve, reject) => {
        const req = https.request(options, (res) => {
            let data = '';
            
            res.on('data', (chunk) => {
                data += chunk;
            });
            
            res.on('end', () => {
                resolve({
                    statusCode: res.statusCode,
                    headers: res.headers,
                    body: data
                });
            });
        });
        
        req.on('error', (error) => {
            reject(error);
        });
        
        if (postData) {
            req.write(postData);
        }
        
        req.end();
    });
}

async function testPayPalCredentials() {
    try {
        // Primeiro: obter access token
        console.log('\n🔑 Obtendo access token...');
        
        const tokenOptions = {
            hostname: 'api.paypal.com',
            port: 443,
            path: '/v1/oauth2/token',
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Accept-Language': 'en_US',
                'Authorization': `Basic ${auth}`,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        };
        
        const tokenResponse = await makeRequest(tokenOptions, 'grant_type=client_credentials');
        
        console.log('Status Code:', tokenResponse.statusCode);
        
        if (tokenResponse.statusCode === 200) {
            const tokenData = JSON.parse(tokenResponse.body);
            console.log('✅ Token obtido com sucesso!');
            console.log('Token Type:', tokenData.token_type);
            console.log('Expires in:', tokenData.expires_in, 'segundos');
            
            // Segundo: criar ordem de teste
            console.log('\n📋 Criando ordem de teste...');
            
            const orderOptions = {
                hostname: 'api.paypal.com',
                port: 443,
                path: '/v2/checkout/orders',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${tokenData.access_token}`,
                    'Accept': 'application/json',
                    'Prefer': 'return=representation'
                }
            };
            
            const orderData = JSON.stringify({
                intent: 'CAPTURE',
                purchase_units: [
                    {
                        amount: {
                            currency_code: 'BRL',
                            value: '100.00'
                        },
                        description: 'Teste de credenciais PayPal'
                    }
                ]
            });
            
            const orderResponse = await makeRequest(orderOptions, orderData);
            
            console.log('Status Code:', orderResponse.statusCode);
            
            if (orderResponse.statusCode === 201) {
                const orderResult = JSON.parse(orderResponse.body);
                console.log('\n✅ SUCESSO! Ordem criada com sucesso!');
                console.log('Order ID:', orderResult.id);
                console.log('Status:', orderResult.status);
                
                // Verificar se tem link de aprovação
                const approveLink = orderResult.links?.find(link => link.rel === 'approve');
                if (approveLink) {
                    console.log('✅ Link de aprovação:', approveLink.href);
                }
                
                console.log('\n🚀 RESULTADO: Credenciais PayPal são VÁLIDAS!');
                console.log('✅ Pode configurar no Railway com segurança!');
                return true;
                
            } else {
                console.log('\n❌ ERRO ao criar ordem:');
                console.log('Response Body:', orderResponse.body);
                return false;
            }
            
        } else {
            console.log('\n❌ ERRO ao obter token:');
            console.log('Response Body:', tokenResponse.body);
            
            if (tokenResponse.statusCode === 401) {
                console.log('\n🔑 PROBLEMA: Credenciais inválidas!');
                console.log('Verifique se Client ID e Secret estão corretos.');
            }
            
            return false;
        }
        
    } catch (error) {
        console.log('\n❌ ERRO na conexão:');
        console.log('Erro:', error.message);
        return false;
    }
}

// Executar teste
testPayPalCredentials()
    .then(success => {
        if (success) {
            console.log('\n🎯 CONCLUSÃO: Credenciais FUNCIONAM - Pode usar no Railway!');
            console.log('📋 Próximos passos:');
            console.log('1. Configurar variáveis no Railway');
            console.log('2. Implementar endpoints do PayPal');
            console.log('3. Adicionar botão no frontend');
        } else {
            console.log('\n💥 CONCLUSÃO: Credenciais INVÁLIDAS - Verificar configuração');
        }
        process.exit(success ? 0 : 1);
    })
    .catch(error => {
        console.error('\n💥 ERRO CRÍTICO:', error);
        process.exit(1);
    });