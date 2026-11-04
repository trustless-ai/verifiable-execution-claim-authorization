// No HTTP network, fork, production key, or public transaction route.
export default {
  networks: {
    laboratory: {
      type: 'edr-simulated', chainType: 'l1', chainId: 31337,
      hardfork: 'shanghai', initialDate: '2026-01-01T00:00:00Z',
      allowBlocksWithSameTimestamp: true,
      throwOnTransactionFailures: false, loggingEnabled: false,
    },
  },
};
