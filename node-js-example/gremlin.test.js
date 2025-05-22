import test from 'ava';
import { makeD3Els, rankMostTraffic, populateGraph } from './gremlin.js';

test('makeD3Els turns single-val maps into primitives', t => {
    const vData = [new Map([['id', ['u1']], ['name', ['Alice']]])];
    const eData = [new Map([
        ['IN', ['u1']], ['OUT', ['u2']],
        ['transactionId', ['T1']], ['amount', [100]]
    ])];

    const { nodes, links } = makeD3Els(vData, eData);
    t.deepEqual(nodes, [{
        id: 'u1', label: 'Alice', data: { id: 'u1', name: 'Alice' }
    }]);
});

test('rankMostTraffic sorts and slices correctly', async t => {
    const A1 = new Map([['accountId','A1'], ['totalAmount', 100]]);
    const A2 = new Map([['accountId','A2'], ['totalAmount', 200]]);
    const fakeG = { V: () => ({ hasLabel: () => ({ project: () => ({ toList: async () => [A1, A2] }) }) }) };

    const top = await rankMostTraffic(fakeG, 1);
    t.is(top.length, 1);
    t.is(top[0].get('accountId'), 'A2');
});
