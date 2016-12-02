## Fake Bittrex

The container mocks out the bittrex exchange rate service.

The contents of data.json are returned when a http
request is made to `fake-bittrex:8003/data`

This should be expanded to include the loggly, segment and lbry.io
requests.  Ideally all of lbry-in-a-box could run without network
access.