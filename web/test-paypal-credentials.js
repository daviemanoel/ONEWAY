const { Client, Environment, LogLevel } = require('@paypal/paypal-server-sdk');

// Credenciais fornecidas pelo usuário
const CLIENT_ID = 'AZV4ztJGO93BrofKtimax5JhqR4vCw3OSyQouUNIhQselj_50f40ck8ft7bNctLazK9iW9fXPXG53dOp';
const CLIENT_SECRET = 'EBQmhC4lNgBrZufvBGtDWBBunBns10jnVp5TCAUrDVq9JY-NfPOV81xMzNfB1foa4EPqC5dYr3_aJ39i';

// Criar cliente PayPal
const paypalClient = new Client({
    clientCredentialsAuthCredentials: {
        oAuthClientId: CLIENT_ID,
        oAuthClientSecret: CLIENT_SECRET
    },
    environment: Environment.Sandbox,
    logging: {
        logLevel: LogLevel.Info,
        logRequest: {
            logBody: true
        },
        logResponse: {
            logHeaders: true
        }
    }
});

async function testPayPalCredentials() {
    console.log('🔍 Testando credenciais PayPal...');
    console.log('Client ID:', CLIENT_ID);
    console.log('Environment: Sandbox');
    
    try {
        // Criar uma ordem de teste simples
        const orderRequest = {
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
        };
        
        console.log('\n📋 Criando ordem de teste...');
        const { ordersController } = paypalClient;
        const order = await ordersController.ordersCreate({
            body: orderRequest,
            prefer: 'return=representation'
        });
        
        if (order.statusCode === 201) {
            console.log('\n✅ SUCESSO! Credenciais PayPal são válidas.');
            console.log('Order ID:', order.result.id);
            console.log('Status:', order.result.status);
            console.log('Links:', order.result.links?.length || 0, 'links disponíveis');
            
            // Verificar se tem link de aprovação
            const approveLink = order.result.links?.find(link => link.rel === 'approve');
            if (approveLink) {
                console.log('✅ Link de aprovação encontrado:', approveLink.href);
            }
            
            console.log('\n🚀 Pode configurar no Railway com segurança!');
            return true;
        } else {
            console.log('\n❌ ERRO: Resposta inesperada');
            console.log('Status Code:', order.statusCode);
            console.log('Response:', order.result);
            return false;
        }
        
    } catch (error) {
        console.log('\n❌ ERRO ao testar credenciais PayPal:');
        console.log('Tipo:', error.constructor.name);
        console.log('Mensagem:', error.message);
        
        if (error.statusCode) {
            console.log('Status Code:', error.statusCode);
        }
        
        if (error.result) {
            console.log('Detalhes do erro:', JSON.stringify(error.result, null, 2));
        }
        
        // Verificar tipos específicos de erro
        if (error.message.includes('authentication') || error.message.includes('unauthorized')) {
            console.log('\n🔑 Problema: Credenciais inválidas ou expiradas');
        } else if (error.message.includes('network') || error.message.includes('timeout')) {
            console.log('\n🌐 Problema: Conectividade ou timeout');
        } else {
            console.log('\n⚠️ Problema: Erro desconhecido - verifique logs acima');
        }
        
        return false;
    }
}

// Executar teste
testPayPalCredentials()
    .then(success => {
        if (success) {
            console.log('\n🎯 RESULTADO: Credenciais VÁLIDAS - Pode usar no Railway!');
        } else {
            console.log('\n💥 RESULTADO: Credenciais INVÁLIDAS - Verificar configuração');
        }
        process.exit(success ? 0 : 1);
    })
    .catch(error => {
        console.error('\n💥 ERRO CRÍTICO:', error);
        process.exit(1);
    });