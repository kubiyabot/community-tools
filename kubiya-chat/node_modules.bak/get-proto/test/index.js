'use strict';

var test = require('tape');

var getProto = require('../');

test('getProto', function (t) {
	t.equal(typeof getProto, 'function', 'is a function');

	t.test('can get', { skip: !getProto }, function (st) {
		var proto = { b: 2 };
		var obj = { a: 1, __proto__: proto };

		// eslint-disable-next-line no-extra-parens
		st.equal(/** @type {NonNullable<typeof getProto>} */ (getProto)(obj), proto, 'obj: returns the [[Prototype]]');

		// eslint-disable-next-line no-extra-parens
		st.equal(/** @type {NonNullable<typeof getProto>} */ (getProto)(proto), Object.prototype, 'proto: returns the [[Prototype]]');

		st.end();
	});

	t.test('can not get', { skip: !!getProto }, function (st) {
		st.equal(getProto, null);

		st.end();
	});

	t.end();
});
