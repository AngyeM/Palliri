var redis = require("redis"),
redis_cli = redis.createClient();
var cron = require('node-cron');
var async = require('async');
var eachLimit=require('async/eachLimit');
var spawn = require('child_process').spawn;
const express = require("express");
const fs = require("fs")

app=express();


db.select(1, function(err,res){
  db.set('key', 'string'); 
});

//https://scotch.io/tutorials/nodejs-cron-jobs-by-examples
cron.schedule('*/5 * * * *', function() {
     console.log("Crawling every 5 minutes")
     redis_cli.smembers("estado:0", function (err, replies) {
        crawl(replies)
        console.log(replies)
     });
  }
);

app.listen(3128);

function crawl(urls_array) {
  async.each(urls_array.slice(0,4),function(url,callback){
    redis_cli.hgetall(url,function(err,obj){
      console.log("processing "+obj.metadata_id+url);
      spawn('python',["../crawl/task.py",url] ,{stdio: 'ignore',detached: true}).unref();
    });
  });
}
